import time
from typing import Dict, Any, Optional
from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE, DATABASE_PATH
from .schemas import EstimationResult
from .retriever import HistoricalRetriever
from .prompts import SYSTEM_PROMPT, build_zero_shot_prompt, build_few_shot_prompt

class StoryPointAgent:
    """
    Agente de IA para Estimativa de Story Points utilizando modelos OpenAI com saídas estruturadas.
    Suporta tanto o modo Zero-Shot quanto Few-Shot (com calibração histórica via SQLite).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = OPENAI_MODEL,
        temperature: float = TEMPERATURE,
        db_path: str = DATABASE_PATH,
        mock_mode: bool = False
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        self.mock_mode = mock_mode
        self.retriever = HistoricalRetriever(db_path=db_path)

        if not self.mock_mode and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def estimate(
        self,
        target_issue: Dict[str, Any],
        mode: str = "few-shot",
        k_anchors: int = 4
    ) -> EstimationResult:
        """
        Executa a estimativa para uma issue no modo especificado ('zero-shot' ou 'few-shot').
        """
        if self.mock_mode or not self.client:
            return self._mock_estimate(target_issue, mode=mode)

        project_stats = self.retriever.get_project_stats(target_issue.get("project_id", 0))

        if mode == "few-shot":
            anchors = self.retriever.retrieve_few_shot_anchors(target_issue, k=k_anchors)
            user_prompt = build_few_shot_prompt(target_issue, anchors, project_stats)
        else:
            user_prompt = build_zero_shot_prompt(target_issue, project_stats)

        # Chamada à OpenAI com Structured Outputs garantindo tipagem forte
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            response_format=EstimationResult
        )

        result = completion.choices[0].message.parsed
        return result

    def _mock_estimate(self, target_issue: Dict[str, Any], mode: str) -> EstimationResult:
        """
        Estimador mock heurístico para testes unitários, validação da esteira e execução offline.
        """
        issue_type = target_issue.get("type", "Task")
        desc = target_issue.get("description_text", "")
        desc_len = len(desc)

        # Heurística baseada em tipo e tamanho da descrição
        if issue_type == "Bug":
            sp = 2.0 if desc_len < 200 else 3.0
            complexity = "Low" if desc_len < 200 else "Medium"
        elif issue_type == "Epic":
            sp = 8.0 if desc_len < 300 else 13.0
            complexity = "Very High"
        elif issue_type in ("Improvement", "Story"):
            sp = 3.0 if desc_len < 300 else 5.0
            complexity = "Medium"
        else:
            sp = 3.0
            complexity = "Medium"

        # Simula pequeno ajuste de calibração em modo few-shot
        comparison = None
        if mode == "few-shot":
            comparison = "Calibrado com âncoras históricas do projeto Mesos na faixa similar."

        return EstimationResult(
            estimated_story_points=float(sp),
            confidence=0.85 if mode == "few-shot" else 0.70,
            complexity=complexity,
            rationale=f"[Mock Mode] Estimativa baseada no tipo '{issue_type}' e descrição de {desc_len} caracteres.",
            key_factors=[f"Tipo: {issue_type}", f"Extensão textual: {desc_len} chars"],
            comparison_with_history=comparison
        )
