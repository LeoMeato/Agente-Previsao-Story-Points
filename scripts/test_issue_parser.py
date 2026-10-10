import sys
from test_parser import parse_mysql_insert_line

# Test on line 3347 (Issue)
with open("TAWOS.sql", "r", encoding="utf-8", errors="ignore") as f:
    for i in range(3348):
        line = f.readline()
        if i == 3347:
            print("Testing on Issue line 3347 (length:", len(line), ")")
            rows = []
            for r in parse_mysql_insert_line(line):
                rows.append(r)
                if len(rows) >= 5:
                    break
            print(f"Extracted {len(rows)} issues successfully!")
            for idx, r in enumerate(rows):
                print(f"\n--- Issue {idx+1} (Columns: {len(r)}) ---")
                # ID (0), Key (2), Title (4), Type (8), Story_Point (16), Project_ID (28)
                print(f"ID: {r[0]}")
                print(f"Key: {r[2]}")
                print(f"Title: {r[4]}")
                print(f"Type: {r[8]}")
                print(f"Story_Point: {r[16]}")
                print(f"Project_ID: {r[28]}")
                print(f"Description_Text (sample): {str(r[6])[:100]}")
                print(f"Changes: Title_Changed={r[21]}, Desc_Changed={r[22]}, SP_Changed={r[23]}")
            break
