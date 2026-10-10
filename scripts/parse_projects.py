import re

# Line 4463 has all projects
with open("TAWOS.sql", "r", encoding="utf-8", errors="ignore") as f:
    for i in range(4464):
        line = f.readline()
        if i == 4463:
            # line 4463 contains INSERT INTO `Project` VALUES (...)
            # Schema: ID, Project_Key, Name, URL, Description, Start_Date, Last_Update_Date, SP_Field_ID, Repository_ID
            print("Project line length:", len(line))
            # Let's extract values
            # Using regex or simple parsing
            matches = re.findall(r"\((\d+),'([^']*)','([^']*)',", line)
            print(f"\nFound {len(matches)} projects:")
            print(f"{'ID':<5} {'Key':<15} {'Name'}")
            print("-" * 50)
            for m in matches:
                print(f"{m[0]:<5} {m[1]:<15} {m[2]}")
            break
