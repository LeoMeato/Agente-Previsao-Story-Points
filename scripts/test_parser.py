import sys

def parse_mysql_insert_line(line):
    """
    Parses a single MySQL INSERT INTO ... VALUES (...) line.
    Yields list of values for each row tuple.
    """
    # Find start of VALUES
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

        # We are inside a row
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

        # Not in string
        if c == "'":
            in_str = True
            val_chars = []
        elif c == ',':
            # End of field
            v_str = "".join(val_chars).strip()
            if v_str == "NULL" or v_str == "null":
                row.append(None)
            elif not val_chars and not in_str: # empty
                row.append(None)
            else:
                row.append(v_str)
            val_chars = []
        elif c == ')':
            # End of row
            v_str = "".join(val_chars).strip()
            if v_str == "NULL" or v_str == "null":
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

# Test on line 4463 (Project)
with open("TAWOS.sql", "r", encoding="utf-8", errors="ignore") as f:
    for i in range(4464):
        line = f.readline()
        if i == 4463:
            print("Testing on Project line (length:", len(line), ")")
            rows = list(parse_mysql_insert_line(line))
            print(f"Extracted {len(rows)} projects successfully!")
            for r in rows[:5]:
                print(r)
            break
