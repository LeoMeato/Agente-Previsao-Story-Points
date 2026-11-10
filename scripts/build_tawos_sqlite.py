import os
import sys
import sqlite3
import time
from collections import defaultdict

def parse_mysql_insert_line(line):
    values_idx = line.find("VALUES")
    if values_idx == -1:
        values_idx = line.find("values")
        if values_idx == -1:
            return
    idx = values_idx + 6
    n = len(line)

    row = []
    val_chars = []
    in_str = False
    escape = False
    in_row = False

    while idx < n:
        c = line[idx]

        if not in_row:
            if c == '(':
                in_row = True
                row = []
                val_chars = []
                in_str = False
                escape = False
            idx += 1
            continue

        if in_str:
            if escape:
                if c == 'n':
                    val_chars.append('\n')
                elif c == 'r':
                    val_chars.append('\r')
                elif c == 't':
                    val_chars.append('\t')
                elif c == '\\':
                    val_chars.append('\\')
                elif c == "'":
                    val_chars.append("'")
                elif c == '"':
                    val_chars.append('"')
                elif c == '0':
                    val_chars.append('\0')
                else:
                    val_chars.append(c)
                escape = False
            elif c == '\\':
                escape = True
            elif c == "'":
                in_str = False
            else:
                val_chars.append(c)
            idx += 1
            continue

        if c == "'":
            in_str = True
            val_chars = []
        elif c == ',':
            v_str = "".join(val_chars).strip()
            if v_str.upper() == "NULL" or (not val_chars and not in_str):
                row.append(None)
            else:
                row.append(v_str)
            val_chars = []
        elif c == ')':
            v_str = "".join(val_chars).strip()
            if v_str.upper() == "NULL":
                row.append(None)
            elif val_chars or in_str:
                row.append(v_str)
            else:
                row.append(None)
            yield row
            row = []
            val_chars = []
            in_row = False
        else:
            val_chars.append(c)
        idx += 1

def main():
    sql_file = "TAWOS.sql"
    db_file = "tawos.db"

    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed previous {db_file}")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # Create tables
    cur.execute("""
    CREATE TABLE project (
        id INTEGER PRIMARY KEY,
        project_key TEXT,
        name TEXT,
        url TEXT,
        description TEXT,
        start_date TEXT,
        last_update_date TEXT,
        sp_field_id TEXT,
        repository_id INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE issue (
        id INTEGER PRIMARY KEY,
        jira_id INTEGER,
        issue_key TEXT,
        url TEXT,
        title TEXT,
        description TEXT,
        description_text TEXT,
        description_code TEXT,
        type TEXT,
        priority TEXT,
        status TEXT,
        resolution TEXT,
        creation_date TEXT,
        estimation_date TEXT,
        resolution_date TEXT,
        last_updated TEXT,
        story_point REAL,
        timespent REAL,
        in_progress_minutes REAL,
        total_effort_minutes REAL,
        resolution_time_minutes REAL,
        title_changed_after_estimation INTEGER,
        description_changed_after_estimation INTEGER,
        story_point_changed_after_estimation INTEGER,
        pull_request_url TEXT,
        creator_id INTEGER,
        reporter_id INTEGER,
        assignee_id INTEGER,
        project_id INTEGER,
        sprint_id INTEGER,
        comment_count INTEGER DEFAULT 0
    );
    """)

    cur.execute("""
    CREATE TABLE comment (
        id INTEGER PRIMARY KEY,
        comment TEXT,
        comment_text TEXT,
        comment_code TEXT,
        creation_date TEXT,
        author_id INTEGER,
        issue_id INTEGER
    );
    """)

    conn.commit()

    print("Step 1: Reading Project and Issues with Story Points...")
    start_time = time.time()

    valid_issue_ids = set()
    issues_to_insert = []
    projects_to_insert = []

    with open(sql_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f):
            # Check table inserts
            if line.startswith("INSERT INTO `Project`"):
                for r in parse_mysql_insert_line(line):
                    projects_to_insert.append(r[:9])
            elif line.startswith("INSERT INTO `Issue`"):
                for r in parse_mysql_insert_line(line):
                    if len(r) >= 30:
                        sp = r[16]
                        if sp is not None and sp != "NULL" and sp != "":
                            try:
                                sp_val = float(sp)
                                if sp_val > 0:
                                    issue_id = int(r[0])
                                    valid_issue_ids.add(issue_id)
                                    row_data = list(r[:30]) + [0]
                                    issues_to_insert.append(row_data)
                                    if len(issues_to_insert) >= 5000:
                                        cur.executemany("INSERT INTO issue VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", issues_to_insert)
                                        conn.commit()
                                        issues_to_insert = []
                            except ValueError:
                                pass

            if line_num % 500 == 0 and line_num > 0:
                print(f"Scanned {line_num} lines... ({len(valid_issue_ids)} issues with SP found)")

    if issues_to_insert:
        cur.executemany("INSERT INTO issue VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", issues_to_insert)
        conn.commit()
        issues_to_insert = []

    print(f"\nInserting {len(projects_to_insert)} projects...")
    cur.executemany("INSERT INTO project VALUES (?,?,?,?,?,?,?,?,?)", projects_to_insert)
    conn.commit()
    print(f"Step 1 completed in {time.time() - start_time:.1f}s. Total issues with SP: {len(valid_issue_ids)}")

    print("\nStep 2: Reading Comments for estimated issues...")
    start_time_c = time.time()
    comments_to_insert = []
    comment_counts = defaultdict(int)
    total_comments_inserted = 0

    with open(sql_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f):
            if line_num < 1950:
                continue
            if line_num > 3255:
                break
            if line.startswith("INSERT INTO `Comment`"):
                for r in parse_mysql_insert_line(line):
                    if len(r) >= 7 and r[6] is not None:
                        try:
                            iss_id = int(r[6])
                            if iss_id in valid_issue_ids:
                                comments_to_insert.append(r[:7])
                                comment_counts[iss_id] += 1
                                if len(comments_to_insert) >= 10000:
                                    cur.executemany("INSERT INTO comment VALUES (?,?,?,?,?,?,?)", comments_to_insert)
                                    conn.commit()
                                    total_comments_inserted += len(comments_to_insert)
                                    comments_to_insert = []
                        except ValueError:
                            pass
            if line_num % 200 == 0:
                print(f"Processed comment line {line_num} / 3255... ({total_comments_inserted + len(comments_to_insert)} comments matched)")

    if comments_to_insert:
        cur.executemany("INSERT INTO comment VALUES (?,?,?,?,?,?,?)", comments_to_insert)
        conn.commit()
        total_comments_inserted += len(comments_to_insert)
        comments_to_insert = []

    print(f"Inserted {total_comments_inserted} comments in {time.time() - start_time_c:.1f}s.")

    print("Updating comment_count column in issue table...")
    update_data = [(count, iss_id) for iss_id, count in comment_counts.items()]
    cur.executemany("UPDATE issue SET comment_count = ? WHERE id = ?", update_data)
    conn.commit()

    print("Creating indexes...")
    cur.execute("CREATE INDEX idx_issue_project ON issue(project_id);")
    cur.execute("CREATE INDEX idx_issue_type ON issue(type);")
    cur.execute("CREATE INDEX idx_comment_issue ON comment(issue_id);")
    conn.commit()
    conn.close()

    db_size_mb = os.path.getsize(db_file) / (1024 * 1024)
    print(f"\nSUCCESS! Database created at '{db_file}' (Size: {db_size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
