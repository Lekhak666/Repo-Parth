from collections import defaultdict


def build_project_structure(files: list[dict]) -> dict:
    structure = defaultdict(list)

    for file in files:
        path = file["path"]

        parts = path.split("/")

        if len(parts) == 1:
            structure["root"].append(parts[0])
        else:
            top_level = parts[0]

            if parts[1] not in structure[top_level]:
                structure[top_level].append(parts[1])

    return dict(structure)