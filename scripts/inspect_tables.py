import re
import os
import sys

sql_path = "TAWOS.sql"

if not os.path.exists(sql_path):
    print(f"Error: {sql_path} not found.")
    sys.exit(1)

print(f"Analyzing {sql_path} structure...")

tables = {}
current_table = None
in_create_table = False

# We'll read line by line to discover CREATE TABLE blocks
# Also check encoding handling
with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
    for line_num, line in enumerate(f):
        # Look for CREATE TABLE
        match_create = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([a-zA-Z0-9_]+)`?", line, re.IGNORECASE)
        if match_create:
            current_table = match_create.group(1)
            tables[current_table] = []
            in_create_table = True
            continue

        if in_create_table:
            # Check for end of CREATE TABLE
            if line.strip().startswith(")") or ");" in line:
                in_create_table = False
                current_table = None
            else:
                col_match = re.match(r"\s*`?([a-zA-Z0-9_]+)`?\s+([a-zA-Z0-9_()]+)", line)
                if col_match and current_table:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2)
                    if col_name.upper() not in ("PRIMARY", "KEY", "CONSTRAINT", "UNIQUE", "FOREIGN"):
                        tables[current_table].append((col_name, col_type))

        # We can stop or pause once we see the first INSERT INTO if all tables are defined at top,
        # but let's see how far the DDL statements go. Usually all CREATE TABLEs are at the beginning.
        # If we see multiple INSERT INTO statements after line 50000 and we haven't seen a new CREATE TABLE in 10000 lines, we can break.
        if line.strip().upper().startswith("INSERT INTO") and len(tables) > 0 and line_num > 50000:
            # Check if this dump has all tables created before inserts or interspersed
            # In mysqldump, tables are usually created right before their inserts (DROP TABLE, CREATE TABLE, INSERT INTO).
            pass

print("\n--- TABLES FOUND ---")
for t_name, cols in tables.items():
    print(f"\nTable: {t_name} ({len(cols)} columns)")
    for col_name, col_type in cols[:10]:
        print(f"  - {col_name} ({col_type})")
    if len(cols) > 10:
        print(f"  ... and {len(cols) - 10} more columns")
