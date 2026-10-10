import re

print("Scanning for INSERT statements...")
seen_tables = set()

with open("TAWOS.sql", "r", encoding="utf-8", errors="ignore") as f:
    for line_num, line in enumerate(f):
        m = re.match(r"\s*INSERT\s+INTO\s+[`\"]?([a-zA-Z0-9_]+)[`\"]?", line, re.IGNORECASE)
        if m:
            table_name = m.group(1)
            if table_name not in seen_tables:
                seen_tables.add(table_name)
                print(f"Line {line_num}: INSERT INTO `{table_name}`")
