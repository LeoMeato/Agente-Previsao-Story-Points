import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from .estimator import StoryPointAgent
from .retriever import HistoricalRetriever
from .schemas import EvaluationRecord
from .utils import calculate_metrics

class AgentEvaluator:
    """
    Pipeline de avaliação empírica para responder sistematicamente às Perguntas de Pesquisa:
    - RQ1: Precisão geral (MAE, Mediana, Desvio Padrão)
    - RQ2: Discrepâncias por falta de informação (descrição ausente, zero comentários, mudanças)
    - RQ3: Impacto do tipo de tarefa (Bug vs Task vs Improvement vs Story)
    """

    def __init__(self, agent: StoryPointAgent, retriever: HistoricalRetriever):
        self.agent = agent
        self.retriever = retriever

    def evaluate_sample(
        self,
        issues: List[Dict[str, Any]],
        mode: str = "few-shot",
        verbose: bool = True
    ) -> List[EvaluationRecord]:
        """Executa a estimativa sobre uma lista de issues e coleta os registros estruturados."""
        records: List[EvaluationRecord] = []
        total = len(issues)

        if verbose:
            print(f"\n[Evaluator] Iniciando avaliação de {total} issues em modo '{mode}'...")

        for idx, issue in enumerate(issues, 1):
            start_t = time.time()
            try:
                res = self.agent.estimate(issue, mode=mode)
                exec_time = time.time() - start_t
                actual_sp = float(issue.get("story_point", 0.0))
                pred_sp = float(res.estimated_story_points)
                abs_err = abs(pred_sp - actual_sp)

                record = EvaluationRecord(
                    issue_id=int(issue["id"]),
                    issue_key=str(issue.get("issue_key", "")),
                    project_key=str(issue.get("project_key", "")),
                    issue_type=str(issue.get("type", "Task")),
                    priority=str(issue.get("priority", "Major")),
                    actual_story_points=actual_sp,
                    predicted_story_points=pred_sp,
                    absolute_error=round(abs_err, 2),
                    mode=mode,
                    confidence=float(res.confidence),
                    complexity=str(res.complexity),
                    has_empty_description=(len(issue.get("description_text", "").strip()) == 0),
                    comment_count=int(issue.get("comment_count", 0)),
                    has_zero_comments=(int(issue.get("comment_count", 0)) == 0),
                    title_changed_after_estimation=bool(issue.get("title_changed_after_estimation", 0)),
                    desc_changed_after_estimation=bool(issue.get("description_changed_after_estimation", 0)),
                    sp_changed_after_estimation=bool(issue.get("story_point_changed_after_estimation", 0)),
                    execution_time_seconds=round(exec_time, 2),
                    rationale=res.rationale
                )
                records.append(record)

                if verbose:
                    print(
                        f"  [{idx}/{total}] {record.issue_key} ({record.issue_type}) -> "
                        f"Real: {actual_sp} | Pred: {pred_sp} | Erro: {abs_err:.1f} pts "
                        f"({exec_time:.2f}s)"
                    )
            except Exception as e:
                if verbose:
                    print(f"  [{idx}/{total}] ERRO ao estimar {issue.get('issue_key')}: {e}")

        return records

    def generate_research_report(self, records: List[EvaluationRecord]) -> Dict[str, Any]:
        """Consolida os dados para responder diretamente às RQ1, RQ2 e RQ3."""
        if not records:
            return {}

        df = pd.DataFrame([r.model_dump() for r in records])

        # RQ1: Precisão Geral
        rq1_metrics = calculate_metrics(df.to_dict(orient="records"))

        # RQ2: Discrepâncias e Contextos de Informação
        rq2_results = {
            "by_description": {
                "empty_description": calculate_metrics(df[df["has_empty_description"]].to_dict(orient="records")),
                "with_description": calculate_metrics(df[~df["has_empty_description"]].to_dict(orient="records"))
            },
            "by_comments": {
                "zero_comments": calculate_metrics(df[df["has_zero_comments"]].to_dict(orient="records")),
                "with_comments": calculate_metrics(df[~df["has_zero_comments"]].to_dict(orient="records"))
            },
            "by_post_estimation_changes": {
                "title_changed": calculate_metrics(df[df["title_changed_after_estimation"]].to_dict(orient="records")),
                "sp_changed": calculate_metrics(df[df["sp_changed_after_estimation"]].to_dict(orient="records"))
            }
        }

        # RQ3: Impacto do Tipo de Tarefa
        rq3_results = {}
        for itype, group in df.groupby("issue_type"):
            rq3_results[itype] = calculate_metrics(group.to_dict(orient="records"))

        return {
            "metadata": {
                "total_issues": len(records),
                "mode": records[0].mode if records else "unknown",
                "timestamp": datetime.now().isoformat()
            },
            "RQ1_General_Accuracy": rq1_metrics,
            "RQ2_Context_Discrepancies": rq2_results,
            "RQ3_Task_Type_Impact": rq3_results
        }

    def save_results(
        self,
        records: List[EvaluationRecord],
        output_dir: str = "results"
    ) -> Dict[str, str]:
        """Salva os registros individuais em CSV e o relatório analítico das RQs em JSON."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = records[0].mode if records else "eval"

        csv_filename = os.path.join(output_dir, f"eval_{mode}_{timestamp}.csv")
        json_filename = os.path.join(output_dir, f"report_{mode}_{timestamp}.json")

        # Salva CSV
        df = pd.DataFrame([r.model_dump() for r in records])
        df.to_csv(csv_filename, index=False, encoding="utf-8")

        # Salva Relatório JSON
        report = self.generate_research_report(records)
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return {
            "csv_path": csv_filename,
            "json_path": json_filename
        }
