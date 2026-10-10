import sqlite3
import pandas as pd

conn = sqlite3.connect("tawos.db")

print("=== TABLE ROW COUNTS ===")
for table in ["project", "sprint", "issue", "comment"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table:<10}: {count:>8} rows")

print("\n=== TOP PROJECTS BY NUMBER OF ISSUES ESTIMATED ===")
query_top = """
SELECT p.id, p.project_key, p.name, COUNT(i.id) AS issue_count,
       ROUND(AVG(i.story_point), 2) AS avg_sp,
       MIN(i.story_point) AS min_sp,
       MAX(i.story_point) AS max_sp
FROM project p
JOIN issue i ON p.id = i.project_id
GROUP BY p.id
ORDER BY issue_count DESC
LIMIT 10;
"""
df_top = pd.read_sql_query(query_top, conn)
print(df_top.to_string(index=False))

print("\n=== RQ2 VARIABLES VERIFICATION (Issues with/without data) ===")
query_rq2 = """
SELECT 
    COUNT(*) AS total_issues,
    SUM(CASE WHEN description_text IS NULL OR TRIM(description_text) = '' THEN 1 ELSE 0 END) AS empty_description,
    SUM(CASE WHEN comment_count = 0 THEN 1 ELSE 0 END) AS zero_comments,
    SUM(CASE WHEN title_changed_after_estimation = 1 THEN 1 ELSE 0 END) AS title_changed,
    SUM(CASE WHEN description_changed_after_estimation = 1 THEN 1 ELSE 0 END) AS desc_changed,
    SUM(CASE WHEN story_point_changed_after_estimation = 1 THEN 1 ELSE 0 END) AS sp_changed
FROM issue;
"""
df_rq2 = pd.read_sql_query(query_rq2, conn)
print(df_rq2.to_string(index=False))

print("\n=== RQ3 BREAKDOWN (Issues by Type) ===")
query_rq3 = """
SELECT type, COUNT(*) AS count, ROUND(AVG(story_point), 2) AS avg_sp
FROM issue
GROUP BY type
ORDER BY count DESC
LIMIT 10;
"""
df_rq3 = pd.read_sql_query(query_rq3, conn)
print(df_rq3.to_string(index=False))

print("\n=== SAMPLE ISSUES READY FOR AGENT ===")
query_sample = """
SELECT i.id, i.issue_key, p.project_key, i.type, i.title, i.story_point, i.comment_count
FROM issue i
JOIN project p ON i.project_id = p.id
WHERE i.comment_count > 0 AND length(i.description_text) > 50
ORDER BY i.id
LIMIT 5;
"""
df_sample = pd.read_sql_query(query_sample, conn)
print(df_sample.to_string(index=False))

conn.close()
