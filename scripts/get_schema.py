import re

target_tables = ["Issue", "Project", "Comment", "Sprint", "Component"]

found_tables = {}
current_table = None

with open("TAWOS.sql", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`([a-zA-Z0-9_]+)`", line, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            # match case-insensitively with target tables
            for t in target_tables:
                if t.lower() == table_name.lower():
                    current_table = t
                    found_tables[current_table] = [line.strip()]
                    break
            else:
                current_table = None
            continue

        if current_table:
            found_tables[current_table].append(line.strip())
            if line.strip().startswith(")") or ");" in line:
                current_table = None
                if len(found_tables) == len(target_tables):
                    break

for t, lines in found_tables.items():
    print(f"=== SCHEMA FOR {t} ===")
    for l in lines:
        print(l)
    print()
