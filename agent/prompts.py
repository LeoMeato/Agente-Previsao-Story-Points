from typing import Dict, Any, List, Optional
from .utils import clean_text

SYSTEM_PROMPT = """Você é um Agente Especialista em Engenharia de Software Ágil e Scrum Master, especializado em estimativa de esforço relativo (Story Points) em equipes de desenvolvimento de software.

Seu objetivo é analisar tarefas/issues do Jira e estimar com precisão o esforço em Story Points, calibrando sua decisão de acordo com as práticas ágeis e a complexidade técnica:
1. Escala de Story Points: Siga a escala clássica de Fibonacci comumente adotada (1, 2, 3, 5, 8, 13).
   - 1 a 2 pontos: Tarefas simples, alterações pontuais, correções triviais ou documentação de baixo risco.
   - 3 pontos: Tarefas padrão, bem compreendidas, com impacto moderado e testes diretos.
   - 5 pontos: Funcionalidades com maior complexidade, lógica não trivial, múltiplas partes afetadas ou risco moderado.
   - 8 pontos: Tarefas complexas, alterações arquiteturais, alto grau de incerteza ou impacto abrangente no sistema.
   - 13 pontos: Tarefas muito grandes, epics ou refatorações profundas que exigem grande esforço de implementação e validação.
2. Análise de Fatores: Avalie o Tipo (Bug, Task, Improvement, Story), a Prioridade e a clareza da Descrição (além de analisar os comentários reais nas issues de exemplo histórico para fins de calibração).
3. Tratamento de Incerteza: Se a issue tiver descrição escassa ou ausente, reconheça a incerteza nos fatores de risco e estime com base no escopo inferido pelo título e tipo.
4. Responda estritamente no formato estruturado solicitado (Pydantic schema).
"""

def format_issue_card(
    issue: Dict[str, Any],
    show_points: bool = False,
    is_example: Optional[bool] = None,
    max_comment_chars: int = 1000,
    max_comments: int = 5
) -> str:
    """
    Formata os dados de uma issue em formato conciso para o prompt.
    Nas issues passadas como exemplos (is_example=True), inclui os próprios comentários da issue.
    A issue a ser estimada (is_example=False) não inclui comentários nem contagem de comentários.
    """
    if is_example is None:
        is_example = show_points

    desc = issue.get("description_text", "").strip()
    if not desc:
        desc = "[Sem descrição fornecida pelo autor]"
    elif len(desc) > 800:
        desc = desc[:800] + "... [truncado]"

    card = [
        f"- Chave: {issue.get('issue_key', 'N/A')}",
        f"- Projeto: {issue.get('project_name', issue.get('project_key', 'N/A'))}",
        f"- Tipo: {issue.get('type', 'Task')}",
        f"- Prioridade: {issue.get('priority', 'Major')}",
        f"- Título: {issue.get('title', 'Sem título')}",
    ]

    card.append(f"- Descrição:\n  \"\"\"{desc}\"\"\"")

    # Para issues de exemplo, inclui o conteúdo textual dos comentários em vez da contagem
    if is_example:
        raw_comments = issue.get("comments") or []
        if isinstance(raw_comments, str):
            raw_comments = [raw_comments]
        elif not isinstance(raw_comments, list):
            raw_comments = list(raw_comments)

        if raw_comments:
            comment_items = []
            for idx, c in enumerate(raw_comments[:max_comments], 1):
                if isinstance(c, dict):
                    c_str = c.get("comment") or c.get("comment_text") or c.get("text", "")
                elif isinstance(c, (list, tuple)) and len(c) > 0:
                    c_str = str(c[0])
                else:
                    c_str = str(c)
                c_clean = clean_text(c_str).strip()
                if len(c_clean) > max_comment_chars:
                    c_clean = c_clean[:max_comment_chars] + "... [truncado]"
                comment_items.append(f"  {idx}. \"\"\"{c_clean}\"\"\"")

            if len(raw_comments) > max_comments:
                comment_items.append(f"  (... {len(raw_comments) - max_comments} comentários adicionais omitidos)")

            card.append("- Comentários:\n" + "\n".join(comment_items))
        else:
            card.append("- Comentários: [Sem comentários registrados]")

    if show_points:
        card.append(f"- STORY POINTS REAIS: {issue.get('story_point', 'N/A')} pts")

    return "\n".join(card)

def build_zero_shot_prompt(target_issue: Dict[str, Any], project_stats: Dict[str, Any] = None) -> str:
    """Gera o prompt para o modo Zero-Shot."""
    stats_text = ""
    if project_stats:
        stats_text = (
            f"Contexto do Projeto {target_issue.get('project_key', '')}:\n"
            f"- Média histórica da equipe: {project_stats.get('avg_sp', '3.2')} story points por issue.\n\n"
        )

    target_card = format_issue_card(target_issue, show_points=False, is_example=False)

    return f"""{stats_text}Analise a seguinte issue e forneça a estimativa de Story Points:

{target_card}

Calcule o esforço relativo considerando a complexidade técnica, riscos, tipo da issue e escopo descrito.
"""

def build_few_shot_prompt(
    target_issue: Dict[str, Any],
    anchors: List[Dict[str, Any]],
    project_stats: Dict[str, Any] = None
) -> str:
    """Gera o prompt para o modo Few-Shot com âncoras históricas de calibração."""
    stats_text = ""
    if project_stats:
        stats_text = (
            f"Contexto do Projeto {target_issue.get('project_key', '')}:\n"
            f"- Média histórica da equipe: {project_stats.get('avg_sp', '3.2')} story points.\n\n"
        )

    anchors_text = []
    for i, anchor in enumerate(anchors, 1):
        anchors_text.append(f"### Exemplo Histórico {i} (Concluído e Estimado pela Equipe):\n{format_issue_card(anchor, show_points=True, is_example=True)}")

    anchors_block = "\n\n".join(anchors_text)
    target_card = format_issue_card(target_issue, show_points=False, is_example=False)

    return f"""{stats_text}Abaixo estão exemplos reais já estimados e concluídos pela MESMA equipe no passado, servindo como régua de calibração de Story Points:

{anchors_block}

---

### Issue a ser Estimada Agora:
{target_card}

Compare a issue atual com os exemplos históricos acima:
1. Identifique a qual nível de esforço dos exemplos a nova issue mais se assemelha.
2. Calibre os Story Points de acordo com a escala e os padrões observados na equipe.
3. Forneça sua justificativa detalhada e aponte os fatores críticos de decisão.
"""
