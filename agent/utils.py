import re
from typing import List, Dict, Any
import numpy as np

def clean_text(text: Any) -> str:
    """Limpa textos com aspas duplicadas ou formatações herdadas do dump SQL."""
    if text is None:
        return ""
    s = str(text).strip()
    # Remove aspas triplas ou aspas externas comuns do parser SQL
    if s.startswith('"""') and s.endswith('"""'):
        s = s[3:-3].strip()
    elif s.startswith('"') and s.endswith('"'):
        s = s[1:-1].strip()
    elif s.startswith("'") and s.endswith("'"):
        s = s[1:-1].strip()
    
    # Normaliza quebras de linha e espaços múltiplos
    s = re.sub(r'\\n', '\n', s)
    s = re.sub(r'\\t', '\t', s)
    s = re.sub(r'\\"', '"', s)
    return s.strip()

def calculate_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula métricas estatísticas consolidadas a partir dos registros de avaliação.
    Responde à RQ1 (Precisão Geral) e suporta segmentações de RQ2 e RQ3.
    """
    if not records:
        return {
            "total_samples": 0,
            "mae": 0.0,
            "median_ae": 0.0,
            "std_ae": 0.0,
            "exact_match_rate": 0.0,
            "within_1_point_rate": 0.0,
            "mean_confidence": 0.0
        }
    
    actuals = np.array([r["actual_story_points"] for r in records])
    predictions = np.array([r["predicted_story_points"] for r in records])
    errors = np.abs(predictions - actuals)
    
    exact_matches = np.sum(errors == 0)
    within_1 = np.sum(errors <= 1.0)
    confidences = [r.get("confidence", 0.0) for r in records]
    
    return {
        "total_samples": len(records),
        "mae": float(np.mean(errors)),
        "median_ae": float(np.median(errors)),
        "std_ae": float(np.std(errors)),
        "exact_match_rate": float(exact_matches / len(records)),
        "within_1_point_rate": float(within_1 / len(records)),
        "mean_confidence": float(np.mean(confidences)) if confidences else 0.0
    }
