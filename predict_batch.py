#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de predição em lote de Story Points utilizando o agente de IA TAWOS.
Restringe as issues alvo estritamente aos 4 tipos solicitados:
  - Bug
  - Suggestion
  - Improvement
  - Story

A mesma quantidade de issues escolhida pelo usuário é aplicada uniformemente
para cada um dos 4 tipos de issue (ex: N=5 -> 5 de cada tipo = 20 issues no total).
As saídas detalhadas e o relatório analítico são armazenados em arquivo (CSV e JSON).
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Garante suporte a UTF-8 no console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adiciona diretório raiz ao sys.path para importações locais
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agent import StoryPointAgent, HistoricalRetriever
from agent.config import OPENAI_API_KEY, OPENAI_MODEL
from agent.utils import calculate_metrics
from run_agent import predict_issue_with_agent

TARGET_TYPES = ["Bug", "Suggestion", "Improvement", "Story"]


def print_banner():
    print("=" * 75)
    print("  TAWOS Agile AI Agent - Predição em Lote (Batch Prediction)")
    print(f"  Modelo: {OPENAI_MODEL} | Provedor: OpenAI")
    print(f"  Tipos Alvo Restritos: {', '.join(TARGET_TYPES)}")
    print("=" * 75)


def run_prediction_via_cli(
    issue_key: str,
    mode: str,
    mock: bool,
    python_exe: str = sys.executable
) -> Dict[str, Any]:
    """
    Executa a predição chamando run_agent.py via subprocess CLI.
    Útil quando se deseja testar o isolamento do processo do run_agent.
    """
    cmd = [
        python_exe,
        str(BASE_DIR / "run_agent.py"),
        "--issue", issue_key,
        "--mode", mode,
        "--json"
    ]
    if mock:
        cmd.append("--mock")

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"Erro no run_agent CLI para {issue_key}: {proc.stderr.strip()}")

    try:
        return json.loads(proc.stdout)
    except Exception as e:
        raise RuntimeError(f"Falha ao decodificar JSON do run_agent para {issue_key}: {e}\nSaída: {proc.stdout}")


def execute_batch(
    issues: List[Dict[str, Any]],
    mode: str = "few-shot",
    mock: bool = False,
    via_cli: bool = False,
    agent: Optional[StoryPointAgent] = None,
    retriever: Optional[HistoricalRetriever] = None
) -> List[Dict[str, Any]]:
    """
    Executa o agente para todas as issues fornecidas, exibindo progresso em tempo real.
    """
    total = len(issues)
    records: List[Dict[str, Any]] = []

    print(f"\n[+] Iniciando predição de {total} issues em modo [{mode.upper()}]...")
    if via_cli:
        print("    (Modo de execução: Subprocess via run_agent.py CLI)")
    else:
        print("    (Modo de execução: Chamada direta ao run_agent)")
    print("-" * 75)

    for idx, issue in enumerate(issues, 1):
        issue_key = issue.get("issue_key", "UNKNOWN")
        issue_type = issue.get("type", "UNKNOWN")
        actual_sp = float(issue.get("story_point", 0.0))

        start_t = time.time()
        try:
            if via_cli:
                rec = run_prediction_via_cli(issue_key, mode=mode, mock=mock)
            else:
                rec = predict_issue_with_agent(
                    issue_or_key=issue,
                    agent=agent,
                    retriever=retriever,
                    mode=mode,
                    mock=mock
                )
            
            elapsed = time.time() - start_t
            rec["batch_index"] = idx
            rec["timestamp"] = datetime.now().isoformat()
            records.append(rec)

            pred_sp = rec.get("predicted_story_points", 0.0)
            err = rec.get("absolute_error", abs(pred_sp - actual_sp))
            print(
                f"  [{idx:>{len(str(total))}}/{total}] ({issue_type:<11}) {issue_key:<15} "
                f"-> Real: {actual_sp:>4.1f} | Previsto: {pred_sp:>4.1f} | "
                f"Erro: {err:>4.1f} pts ({elapsed:>4.2f}s)"
            )
        except Exception as e:
            print(f"  [{idx:>{len(str(total))}}/{total}] ({issue_type:<11}) {issue_key:<15} -> ERRO: {e}")

    return records


def build_batch_report(
    records: List[Dict[str, Any]],
    count_per_type: int,
    mode: str,
    project_filter: str,
    mock: bool,
    total_time: float
) -> Dict[str, Any]:
    """
    Gera o relatório analítico consolidado e as métricas estratificadas por tipo.
    """
    global_metrics = calculate_metrics(records)

    by_type_metrics: Dict[str, Any] = {}
    for itype in TARGET_TYPES:
        subset = [r for r in records if r.get("issue_type") == itype]
        if subset:
            by_type_metrics[itype] = calculate_metrics(subset)
        else:
            by_type_metrics[itype] = {"total_samples": 0, "mae": 0.0, "message": "Nenhuma issue encontrada"}

    return {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "target_types": TARGET_TYPES,
            "count_per_type": count_per_type,
            "total_issues_analyzed": len(records),
            "mode": mode,
            "mock_mode": mock,
            "project_filter": project_filter,
            "total_execution_time_seconds": round(total_time, 2),
            "average_time_per_issue_seconds": round(total_time / max(len(records), 1), 2)
        },
        "global_summary": global_metrics,
        "metrics_by_type": by_type_metrics,
        "records": records
    }


def save_batch_results(
    records: List[Dict[str, Any]],
    report: Dict[str, Any],
    output_path: Optional[str] = None,
    mode: str = "few-shot"
) -> Dict[str, str]:
    """
    Armazena os resultados em arquivo (CSV detalhado e JSON analítico).
    """
    import pandas as pd

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = BASE_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix.lower() == ".json":
            json_file = out
            csv_file = out.with_suffix(".csv")
        elif out.suffix.lower() == ".csv":
            csv_file = out
            json_file = out.with_suffix(".json")
        else:
            csv_file = Path(f"{output_path}.csv")
            json_file = Path(f"{output_path}.json")
    else:
        csv_file = results_dir / f"batch_predictions_{mode}_{timestamp}.csv"
        json_file = results_dir / f"batch_report_{mode}_{timestamp}.json"

    # Exporta CSV
    csv_rows = []
    for r in records:
        row = dict(r)
        if isinstance(row.get("key_factors"), list):
            row["key_factors"] = "; ".join(row["key_factors"])
        csv_rows.append(row)

    df = pd.DataFrame(csv_rows)
    df.to_csv(csv_file, index=False, encoding="utf-8")

    # Exporta JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return {
        "csv_path": str(csv_file),
        "json_path": str(json_file)
    }


def print_summary_table(report: Dict[str, Any], paths: Dict[str, str]):
    """
    Imprime no console a tabela formatada com o resumo dos resultados da predição em lote.
    """
    meta = report["metadata"]
    glob = report["global_summary"]
    by_type = report["metrics_by_type"]

    print("\n" + "=" * 75)
    print(f"  RESUMO DA AVALIAÇÃO EM LOTE - MODO: {meta['mode'].upper()}")
    print("=" * 75)
    print(f"  Total de Issues Analisadas : {meta['total_issues_analyzed']} ({meta['count_per_type']} por tipo)")
    print(f"  Tempo Total                : {meta['total_execution_time_seconds']}s (Média: {meta['average_time_per_issue_seconds']}s/issue)")
    print(f"  MAE Global (Erro Médio)    : {glob['mae']:.2f} story points")
    print(f"  Mediana do Erro Absoluto   : {glob['median_ae']:.2f} story points")
    print(f"  Desvio Padrão do Erro (SD) : {glob['std_ae']:.2f}")
    print(f"  Taxa de Acerto Exato       : {glob['exact_match_rate'] * 100:.1f}%")
    print(f"  Taxa de Erro <= 1 ponto    : {glob['within_1_point_rate'] * 100:.1f}%")
    print("-" * 75)
    print("  Métricas Estratificadas por Tipo de Tarefa:")
    print(f"  {'Tipo':<14} | {'Qtd':<4} | {'MAE (pts)':<9} | {'Mediana':<7} | {'SD':<6} | {'Acerto Exato':<12} | {'Erro <= 1pt':<11}")
    print("  " + "-" * 71)

    for itype in TARGET_TYPES:
        m = by_type.get(itype, {})
        if m.get("total_samples", 0) > 0:
            print(
                f"  {itype:<14} | {m['total_samples']:<4} | {m['mae']:<9.2f} | "
                f"{m['median_ae']:<7.2f} | {m['std_ae']:<6.2f} | "
                f"{m['exact_match_rate']*100:>10.1f}% | {m['within_1_point_rate']*100:>9.1f}%"
            )
        else:
            print(f"  {itype:<14} | 0    | N/A       | N/A     | N/A    | N/A          | N/A")

    print("=" * 75)
    print("[OK] Saídas armazenadas com sucesso:")
    print(f"  -> Arquivo CSV  : {paths['csv_path']}")
    print(f"  -> Arquivo JSON : {paths['json_path']}")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(
        description="Executa predições em lote do agente TAWOS para os tipos Bug, Suggestion, Improvement e Story."
    )
    parser.add_argument(
        "-n", "--count-per-type", "--quantity",
        dest="count_per_type",
        type=int,
        default=None,
        help="Quantidade de issues a analisar para CADA um dos 4 tipos (Bug, Suggestion, Improvement, Story). Ex: -n 5 analisa 20 issues."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["few-shot", "zero-shot", "both"],
        default="few-shot",
        help="Estratégia de inferência do agente: 'few-shot' (padrão), 'zero-shot' ou 'both'"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Caminho do arquivo de saída (ex: results/minhas_predicoes.csv ou .json). Padrão: results/batch_predictions_<mode>_<timestamp>.csv"
    )
    parser.add_argument(
        "-p", "--project",
        type=str,
        default="ALL",
        help="Filtrar por projeto específico (ex: MESOS, XD, CLOV). Padrão: ALL (busca nos projetos que possuem os tipos alvo)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Executa em modo Mock heurístico (sem realizar chamadas pagas à OpenAI)"
    )
    parser.add_argument(
        "--via-cli",
        action="store_true",
        help="Invoca run_agent.py via subprocess CLI para cada issue, em vez de chamada direta ao agente"
    )
    parser.add_argument(
        "--no-date-filter",
        action="store_true",
        help="Não restringe a amostragem a issues a partir de 2014-01-01"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente pseudo-aleatória determinística para reprodução da amostragem (padrão: 42)"
    )

    args = parser.parse_args()

    # Interatividade para escolha da quantidade, se não informada via CLI
    count_per_type = args.count_per_type
    if count_per_type is None:
        if sys.stdin.isatty():
            try:
                user_input = input("\n[?] Quantas issues deseja analisar por tipo (Bug, Suggestion, Improvement, Story)? [Padrão: 5]: ").strip()
                if user_input:
                    count_per_type = int(user_input)
                else:
                    count_per_type = 5
            except (ValueError, KeyboardInterrupt):
                print("\n[-] Entrada inválida ou cancelada. Utilizando o valor padrão de 5 issues por tipo.")
                count_per_type = 5
        else:
            count_per_type = 5

    if count_per_type <= 0:
        print("[-] Erro: A quantidade por tipo deve ser um número inteiro positivo (>= 1).")
        sys.exit(1)

    print_banner()

    # Aviso sobre API Key
    if not args.mock and not OPENAI_API_KEY:
        print("[!] AVISO: Nenhuma chave OPENAI_API_KEY encontrada no arquivo .env.")
        print("    Para executar sem gastar tokens ou testar a esteira, adicione o parâmetro --mock.")
        print("    Exemplo: python predict_batch.py -n 5 --mock\n")
        if not sys.stdin.isatty():
            sys.exit(1)
        confirm = input("[?] Deseja continuar em modo MOCK? (s/n) [s]: ").strip().lower()
        if confirm in ("", "s", "sim", "y", "yes"):
            args.mock = True
        else:
            print("[-] Execução abortada pelo usuário.")
            sys.exit(1)

    retriever = HistoricalRetriever()
    agent = StoryPointAgent(mock_mode=args.mock)

    total_expected = count_per_type * len(TARGET_TYPES)
    min_date = None if args.no_date_filter else "2014-01-01"

    print(f"\n[+] Coletando amostra de issues do banco tawos.db...")
    print(f"    - Tipos alvo     : {', '.join(TARGET_TYPES)}")
    print(f"    - Qtd por tipo   : {count_per_type}")
    print(f"    - Total esperado : {total_expected} issues ({count_per_type} * 4 tipos)")
    print(f"    - Filtro Projeto : {args.project}")
    print(f"    - Modo Agente    : {args.mode.upper()}")
    print(f"    - Modo Mock      : {'ATIVO' if args.mock else 'INATIVO (OpenAI API)'}")

    # Coleta a amostra balanceada
    issues = retriever.sample_issues_by_types(
        issue_types=TARGET_TYPES,
        count_per_type=count_per_type,
        project_key=args.project,
        min_date=min_date,
        random_seed=args.seed
    )

    if not issues:
        print(f"[-] Nenhuma issue encontrada para os critérios informados (projeto={args.project}).")
        sys.exit(1)

    # Detalha contagem encontrada por tipo
    counts_found = {t: 0 for t in TARGET_TYPES}
    for iss in issues:
        t = iss.get("type")
        if t in counts_found:
            counts_found[t] += 1

    print(f"\n[+] Amostra obtida: {len(issues)} issues no total.")
    for t in TARGET_TYPES:
        status_sym = "[OK]" if counts_found[t] == count_per_type else "[!]"
        print(f"    {status_sym} {t:<12}: {counts_found[t]}/{count_per_type} issues")

    modes_to_run = ["zero-shot", "few-shot"] if args.mode == "both" else [args.mode]

    for mode in modes_to_run:
        start_batch_time = time.time()
        records = execute_batch(
            issues=issues,
            mode=mode,
            mock=args.mock,
            via_cli=args.via_cli,
            agent=agent,
            retriever=retriever
        )
        total_batch_time = time.time() - start_batch_time

        report = build_batch_report(
            records=records,
            count_per_type=count_per_type,
            mode=mode,
            project_filter=args.project,
            mock=args.mock,
            total_time=total_batch_time
        )

        paths = save_batch_results(
            records=records,
            report=report,
            output_path=args.output,
            mode=mode
        )

        print_summary_table(report, paths)


if __name__ == "__main__":
    main()
