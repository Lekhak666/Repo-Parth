from pathlib import Path


def detect_technologies(files: list[dict]) -> list[str]:
    paths = {file["path"].lower() for file in files}

    technologies = []

    # Python
    if any(path.endswith(".py") for path in paths):
        technologies.append("Python")

    # JavaScript / TypeScript
    if any(path.endswith(".js") for path in paths):
        technologies.append("JavaScript")

    if any(path.endswith(".ts") or path.endswith(".tsx") for path in paths):
        technologies.append("TypeScript")

    # React
    if any(
        path.endswith(".tsx")
        or path.endswith(".jsx")
        or "react" in path
        for path in paths
    ):
        technologies.append("React")

    # Django
    if "manage.py" in {Path(path).name.lower() for path in paths}:
        technologies.append("Django")

    # FastAPI
    if any(
        "fastapi" in path
        for path in paths
    ):
        technologies.append("FastAPI")

    # Node.js
    if "package.json" in {Path(path).name.lower() for path in paths}:
        technologies.append("Node.js")

    # PostgreSQL
    if any(
        "postgres" in path or "postgresql" in path
        for path in paths
    ):
        technologies.append("PostgreSQL")

    # Docker
    if any(
        Path(path).name.lower() in {
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
        }
        for path in paths
    ):
        technologies.append("Docker")

    # GitHub Actions
    if any(
        ".github/workflows/" in path
        for path in paths
    ):
        technologies.append("GitHub Actions")

    return technologies