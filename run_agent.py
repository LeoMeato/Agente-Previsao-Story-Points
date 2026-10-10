import argparse
import sys
import json

# Assegura suporte a UTF-8 no console Windows se suportado
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent import StoryPointAgent, HistoricalRetriever, AgentEvaluator
from agent.config import OPENAI_API_KEY, OPENAI_MODEL

def print_banner():
    print("=" * 70)
    print("  TAWOS Agile AI Agent - Estimador de Story Points")
    print(f"  Modelo: {OPENAI_MODEL} | Provedor: OpenAI")
    print("=" * 70)

def handle_single_issue(args, agent, retriever):
    print(f"\n[+] Buscando issue: {args.issue}...")
    issue = retriever.get_issue_by_key(args.issue)
    if not issue:
        print(f"[-] Erro: Issue '{args.issue}' não encontrada no banco tawos.db.")
        sys.exit(1)

    print(f"    Projeto: {issue.get('project_key')} ({issue.get('project_name')})")
    print(f"    Título: {issue.get('title')}")
    print(f"    Tipo: {issue.get('type')} | Prioridade: {issue.get('priority')}")
    print(f"    Story Points Reais da Equipe: {issue.get('story_point')} pts")
    print("-" * 70)

    modes = ["zero-shot", "few-shot"] if args.mode == "both" else [args.mode]
    for mode in modes:
        print(f"\n>>> Executando estimativa em modo [{mode.upper()}]...")
        result = agent.estimate(issue, mode=mode)
        
        diff = abs(result.estimated_story_points - issue.get("story_point", 0.0))
        print(f"  -> Story Points Previstos : {result.estimated_story_points} pts")
        print(f"  -> Confiança              : {result.confidence * 100:.1f}%")
        print(f"  -> Complexidade           : {result.complexity}")
        print(f"  -> Erro Absoluto (|y - y_pred|): {diff:.2f} pts")
        print(f"  -> Rationale / Motivo     : {result.rationale}")
        if result.key_factors:
            print(f"  -> Fatores Chave          : {', '.join(result.key_factors)}")
        if result.comparison_with_history:
            print(f"  -> Calibração Histórica   : {result.comparison_with_history}")
        print("-" * 70)

def handle_benchmark(args, agent, retriever):
    evaluator = AgentEvaluator(agent=agent, retriever=retriever)
    print(f"\n[+] Coletando amostra de {args.sample_size} issues do projeto {args.project}...")
    sample = retriever.sample_evaluation_dataset(
        project_key=args.project,
        sample_size=args.sample_size
    )

    if not sample:
        print(f"[-] Nenhuma issue encontrada para o projeto {args.project}.")
        sys.exit(1)

    print(f"[+] {len(sample)} issues selecionadas para o benchmark.")

    modes_to_run = ["zero-shot", "few-shot"] if args.mode == "both" else [args.mode]

    for mode in modes_to_run:
        print(f"\n{'='*70}")
        print(f"  INICIANDO AVALIAÇÃO: {mode.upper()}")
        print(f"{'='*70}")
        
        records = evaluator.evaluate_sample(sample, mode=mode, verbose=True)
        report = evaluator.generate_research_report(records)
        paths = evaluator.save_results(records)

        # Apresentação dos Resultados
        rq1 = report["RQ1_General_Accuracy"]
        print(f"\n--- [RQ1: Precisão Geral ({mode.upper()})] ---")
        print(f"  Total de Amostras  : {rq1['total_samples']}")
        print(f"  MAE (Erro Médio)   : {rq1['mae']:.2f} story points")
        print(f"  Mediana do Erro    : {rq1['median_ae']:.2f} story points")
        print(f"  Desvio Padrão (SD) : {rq1['std_ae']:.2f}")
        print(f"  Acerto Exato       : {rq1['exact_match_rate'] * 100:.1f}%")
        print(f"  Erro <= 1 ponto    : {rq1['within_1_point_rate'] * 100:.1f}%")

        print("\n--- [RQ2: Discrepâncias de Contexto (MAE)] ---")
        rq2 = report["RQ2_Context_Discrepancies"]
        print(f"  Descrição Vazia ({rq2['by_description']['empty_description']['total_samples']} issues)   : MAE = {rq2['by_description']['empty_description']['mae']:.2f}")
        print(f"  Com Descrição ({rq2['by_description']['with_description']['total_samples']} issues)     : MAE = {rq2['by_description']['with_description']['mae']:.2f}")
        print(f"  Zero Comentários ({rq2['by_comments']['zero_comments']['total_samples']} issues)   : MAE = {rq2['by_comments']['zero_comments']['mae']:.2f}")
        print(f"  Com Comentários ({rq2['by_comments']['with_comments']['total_samples']} issues)    : MAE = {rq2['by_comments']['with_comments']['mae']:.2f}")

        print("\n--- [RQ3: Impacto do Tipo de Tarefa (MAE)] ---")
        rq3 = report["RQ3_Task_Type_Impact"]
        for t_name, t_metrics in rq3.items():
            print(f"  {t_name:<15} ({t_metrics['total_samples']:>2} issues) : MAE = {t_metrics['mae']:.2f} (SD: {t_metrics['std_ae']:.2f})")

        print(f"\n[OK] Arquivos salvos:")
        print(f"    CSV  : {paths['csv_path']}")
        print(f"    JSON : {paths['json_path']}")

def main():
    parser = argparse.ArgumentParser(description="TAWOS Story Point Estimation AI Agent")
    parser.add_argument("--issue", type=str, help="Chave da issue para estimar (ex: MESOS-10175)")
    parser.add_argument("--benchmark", action="store_true", help="Executa o pipeline de avaliação completo (RQ1, RQ2, RQ3)")
    parser.add_argument("--mode", type=str, choices=["zero-shot", "few-shot", "both"], default="few-shot", help="Modo de estimativa")
    parser.add_argument("--project", type=str, default="MESOS", help="Código do projeto (ex: MESOS, XD, EVG)")
    parser.add_argument("--sample-size", type=int, default=10, help="Tamanho da amostra para benchmark")
    parser.add_argument("--mock", action="store_true", help="Executa em modo Mock (sem chamadas à API OpenAI)")

    args = parser.parse_args()

    print_banner()

    # Validação de API Key
    if not args.mock and not OPENAI_API_KEY:
        print("[!] AVISO: Nenhuma chave OPENAI_API_KEY encontrada no arquivo .env ou variáveis de ambiente.")
        print("    Para rodar sem gastar tokens ou testar a esteira, adicione o parâmetro --mock.")
        print("    Exemplo: python run_agent.py --issue MESOS-10175 --mock\n")
        if not args.issue and not args.benchmark:
            parser.print_help()
            sys.exit(1)

    retriever = HistoricalRetriever()
    agent = StoryPointAgent(mock_mode=args.mock)

    if args.issue:
        handle_single_issue(args, agent, retriever)
    elif args.benchmark:
        handle_benchmark(args, agent, retriever)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
