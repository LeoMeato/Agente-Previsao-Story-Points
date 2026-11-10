import sqlite3
from typing import List, Dict, Any, Optional
from .config import DATABASE_PATH
from .utils import clean_text

class HistoricalRetriever:
    """
    Módulo responsável por consultar o banco SQLite (tawos.db) e recuperar
    exemplos históricos do mesmo projeto para calibração de Few-Shot.
    
    Garante rigor metodológico:
    - Zero vazamento temporal (data de criação do exemplo < data de criação da issue avaliada).
    - Exemplos âncora representativos em múltiplos patamares de esforço (baixo, médio, alto).
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_issue_by_key(self, issue_key: str, include_comments: bool = False) -> Optional[Dict[str, Any]]:
        """Recupera uma issue pelo seu issue_key (ex: MESOS-10175)."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT i.*, p.project_key, p.name as project_name
                FROM issue i
                JOIN project p ON i.project_id = p.id
                WHERE i.issue_key = ?
            """, (issue_key,))
            row = cur.fetchone()
            if not row:
                return None
            issue = self._format_issue_row(dict(row))
            if include_comments:
                issue["comments"] = self.get_comments_for_issue(issue["id"], conn=conn)
            return issue

    def get_issue_by_id(self, issue_id: int, include_comments: bool = False) -> Optional[Dict[str, Any]]:
        """Recupera uma issue pelo seu ID numérico."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT i.*, p.project_key, p.name as project_name
                FROM issue i
                JOIN project p ON i.project_id = p.id
                WHERE i.id = ?
            """, (issue_id,))
            row = cur.fetchone()
            if not row:
                return None
            issue = self._format_issue_row(dict(row))
            if include_comments:
                issue["comments"] = self.get_comments_for_issue(issue["id"], conn=conn)
            return issue

    def get_comments_for_issue(
        self,
        issue_id: int,
        limit: Optional[int] = None,
        conn: Optional[sqlite3.Connection] = None
    ) -> List[str]:
        """Recupera os comentários textuais de uma issue ordenados cronologicamente."""
        should_close = False
        if conn is None:
            conn = self.get_connection()
            should_close = True

        try:
            cur = conn.cursor()
            query = """
                SELECT comment, comment_text
                FROM comment
                WHERE issue_id = ?
                ORDER BY creation_date ASC, id ASC
            """
            if limit is not None:
                query += " LIMIT ?"
                cur.execute(query, (issue_id, int(limit)))
            else:
                cur.execute(query, (issue_id,))
            rows = cur.fetchall()
            comments = []
            for r in rows:
                raw_text = r["comment"] if r["comment"] is not None else r["comment_text"]
                cleaned = clean_text(raw_text)
                if cleaned:
                    comments.append(cleaned)
            return comments
        finally:
            if should_close:
                conn.close()

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Calcula estatísticas de story points do projeto para contexto de calibração."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) as total_estimated,
                    ROUND(AVG(story_point), 2) as avg_sp,
                    MIN(story_point) as min_sp,
                    MAX(story_point) as max_sp
                FROM issue
                WHERE project_id = ?
            """, (project_id,))
            row = cur.fetchone()
            return dict(row) if row else {}

    def retrieve_few_shot_anchors(
        self,
        target_issue: Dict[str, Any],
        k: int = 4,
        include_comments: bool = True,
        max_comments: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera k exemplos históricos do mesmo projeto para calibrar a escala de Story Points.
        Seleciona âncoras diversificadas por faixa de esforço (baixo: 1-2, médio: 3-5, alto: 8+)
        priorizando o mesmo tipo de tarefa (Bug, Task, Improvement, etc.)
        sem vazamento temporal (creation_date < target creation_date).
        """
        project_id = target_issue["project_id"]
        creation_date = target_issue.get("creation_date")
        target_type = target_issue.get("type", "Task")
        target_id = target_issue.get("id")

        with self.get_connection() as conn:
            cur = conn.cursor()

            # Âncoras em 3 faixas de complexidade para calibrar a régua da equipe:
            # 1. Pequeno (1 ou 2 pts)
            # 2. Médio (3 ou 5 pts)
            # 3. Grande (8 ou mais pts)
            # 4. Similar por Tipo
            anchors: List[Dict[str, Any]] = []
            seen_ids = {target_id}

            queries = [
                # Âncora Pequena (1-2 pts)
                ("""
                    SELECT i.*, p.project_key, p.name as project_name
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    WHERE i.project_id = ? 
                      AND i.id != ?
                      AND i.creation_date < ?
                      AND i.story_point IN (1.0, 2.0)
                      AND length(i.description_text) > 30
                    ORDER BY (i.type = ?) DESC, i.creation_date DESC
                    LIMIT 1
                """, (project_id, target_id, creation_date, target_type)),

                # Âncora Média (3-5 pts)
                ("""
                    SELECT i.*, p.project_key, p.name as project_name
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    WHERE i.project_id = ? 
                      AND i.id != ?
                      AND i.creation_date < ?
                      AND i.story_point IN (3.0, 5.0)
                      AND length(i.description_text) > 30
                    ORDER BY (i.type = ?) DESC, i.creation_date DESC
                    LIMIT 1
                """, (project_id, target_id, creation_date, target_type)),

                # Âncora Grande (8+ pts)
                ("""
                    SELECT i.*, p.project_key, p.name as project_name
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    WHERE i.project_id = ? 
                      AND i.id != ?
                      AND i.creation_date < ?
                      AND i.story_point >= 8.0
                      AND length(i.description_text) > 30
                    ORDER BY (i.type = ?) DESC, i.creation_date DESC
                    LIMIT 1
                """, (project_id, target_id, creation_date, target_type)),

                # Âncora de Mesmo Tipo (mais recente)
                ("""
                    SELECT i.*, p.project_key, p.name as project_name
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    WHERE i.project_id = ? 
                      AND i.id != ?
                      AND i.creation_date < ?
                      AND i.type = ?
                      AND length(i.description_text) > 30
                    ORDER BY i.creation_date DESC
                    LIMIT 2
                """, (project_id, target_id, creation_date, target_type))
            ]

            for sql, params in queries:
                cur.execute(sql, params)
                rows = cur.fetchall()
                for r in rows:
                    if r["id"] not in seen_ids and len(anchors) < k:
                        seen_ids.add(r["id"])
                        anchors.append(self._format_issue_row(dict(r)))

            # Fallback caso a data seja muito antiga ou faltem exemplos
            if len(anchors) < k:
                cur.execute("""
                    SELECT i.*, p.project_key, p.name as project_name
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    WHERE i.project_id = ? AND i.id != ? AND i.story_point > 0
                    ORDER BY i.id ASC
                    LIMIT ?
                """, (project_id, target_id, k - len(anchors)))
                for r in cur.fetchall():
                    if r["id"] not in seen_ids and len(anchors) < k:
                        seen_ids.add(r["id"])
                        anchors.append(self._format_issue_row(dict(r)))

            if include_comments:
                for anchor in anchors:
                    if "id" in anchor:
                        anchor["comments"] = self.get_comments_for_issue(anchor["id"], limit=max_comments, conn=conn)

            return anchors

    def sample_evaluation_dataset(
        self,
        project_key: str = "MESOS",
        sample_size: int = 50,
        random_seed: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Retorna uma amostra estratificada para responder às RQs:
        - Inclui proporções equilibradas de tipos (RQ3: Bug, Task, Improvement, Story)
        - Inclui variações de contexto (RQ2: descrições vazias vs preenchidas, zero comentários vs comentários)
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Pega issues a partir de 2014 para garantir histórico prévio robusto para o Few-Shot
            cur.execute("""
                SELECT i.*, p.project_key, p.name as project_name
                FROM issue i
                JOIN project p ON i.project_id = p.id
                WHERE p.project_key = ? 
                  AND i.creation_date >= '2014-01-01'
                ORDER BY ((i.id * 1103515245 + 12345) & 2147483647)
                LIMIT ?
            """, (project_key, sample_size))
            
            rows = cur.fetchall()
            return [self._format_issue_row(dict(r)) for r in rows]

    def _format_issue_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Limpa textos e formata campos para o agente."""
        row["title"] = clean_text(row.get("title", ""))
        row["description_text"] = clean_text(row.get("description_text", ""))
        row["type"] = str(row.get("type", "Task")).strip()
        row["priority"] = str(row.get("priority", "Major")).strip()
        row["comment_count"] = int(row.get("comment_count", 0))
        row["story_point"] = float(row.get("story_point", 0.0))
        return row
