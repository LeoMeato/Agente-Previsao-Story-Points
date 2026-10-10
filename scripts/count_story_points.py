import sys
from collections import defaultdict
from test_parser import parse_mysql_insert_line

print("Analyzing Story Points across projects in TAWOS.sql...")

project_total = defaultdict(int)
project_with_sp = defaultdict(int)

# Issue is from line 3347 to 4376
with open("TAWOS.sql", "r", encoding="utf-8", errors="ignore") as f:
    for line_num, line in enumerate(f):
        if line_num < 3347:
            continue
        if line_num > 4376:
            break
        
        if line.startswith("INSERT INTO `Issue`"):
            for row in parse_mysql_insert_line(line):
                # row[28] is Project_ID, row[16] is Story_Point
                if len(row) >= 29:
                    p_id = row[28]
                    sp = row[16]
                    project_total[p_id] += 1
                    if sp is not None and sp != "NULL" and sp != "":
                        try:
                            val = float(sp)
                            if val > 0:
                                project_with_sp[p_id] += 1
                        except ValueError:
                            pass

        if line_num % 100 == 0:
            print(f"Processed line {line_num} / 4376...")

print("\n--- STORY POINTS SUMMARY BY PROJECT ID ---")
for p_id in sorted(project_total.keys(), key=lambda x: int(x) if x and x.isdigit() else 0):
    total = project_total[p_id]
    with_sp = project_with_sp[p_id]
    pct = (with_sp / total * 100) if total > 0 else 0
    print(f"Project_ID: {p_id:<4} Total: {total:<7} With Story Points: {with_sp:<6} ({pct:.1f}%)")
