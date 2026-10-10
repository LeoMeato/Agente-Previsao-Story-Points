from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class EstimationResult(BaseModel):
    """Estrutura formal da saída de estimativa gerada pelo Agente de IA."""
    
    estimated_story_points: float = Field(
        ...,
        description="Valor numérico previsto de story points (geralmente seguindo a escala de Fibonacci: 1, 2, 3, 5, 8, 13)."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Grau de certeza do agente sobre a estimativa (0.0 a 1.0)."
    )
    complexity: Literal["Very Low", "Low", "Medium", "High", "Very High"] = Field(
        ...,
        description="Classificação qualitativa da complexidade técnica percebida da tarefa."
    )
    rationale: str = Field(
        ...,
        description="Justificativa técnica detalhada de como os story points foram calculados a partir dos requisitos e referências."
    )
    key_factors: List[str] = Field(
        default_factory=list,
        description="Fatores críticos identificados (ex: impacto em banco, dependência externa, falta de especificações, etc.)."
    )
    comparison_with_history: Optional[str] = Field(
        default=None,
        description="Como a issue atual se compara com os exemplos históricos fornecidos (quando executado em modo Few-Shot)."
    )

class EvaluationRecord(BaseModel):
    """Registro de avaliação de uma issue individual para análise quantitativa (RQ1, RQ2, RQ3)."""
    
    issue_id: int
    issue_key: str
    project_key: str
    issue_type: str
    priority: str
    actual_story_points: float
    predicted_story_points: float
    absolute_error: float
    mode: Literal["zero-shot", "few-shot", "mock"]
    confidence: float
    complexity: str
    
    # Variáveis da RQ2
    has_empty_description: bool
    comment_count: int
    has_zero_comments: bool
    title_changed_after_estimation: bool
    desc_changed_after_estimation: bool
    sp_changed_after_estimation: bool
    
    # Metadados de execução
    execution_time_seconds: float
    rationale: str
