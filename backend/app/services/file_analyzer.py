from pathlib import Path


def classify_file(path: str) -> str | None:
    filename = Path(path).name.lower()
    normalized_path = path.lower()

    # Project configuration
    if filename in {
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".env.example",
    }:
        return "Project configuration"

    # Django
    if filename == "manage.py":
        return "Django project entry point"

    if filename == "settings.py":
        return "Django application configuration"

    if filename == "urls.py":
        return "Django URL routing"

    # Database / models
    if filename == "models.py":
        return "Database models"

    # API / backend
    if filename in {"views.py", "routes.py", "api.py"}:
        return "Backend API logic"

    # Frontend
    if filename in {"app.tsx", "app.jsx", "app.js"}:
        return "Frontend application entry point"

    if filename in {"main.tsx", "main.jsx", "main.js"}:
        return "Frontend entry point"

    # Documentation
    if filename.startswith("readme"):
        return "Project documentation"

    # GitHub Actions
    if ".github/workflows/" in normalized_path:
        return "CI/CD workflow"

    return None


def find_important_files(files: list[dict]) -> list[dict]:
    important_files = []

    for file in files:
        role = classify_file(file["path"])

        if role:
            important_files.append(
                {
                    "path": file["path"],
                    "role": role,
                    "size": file.get("size"),
                }
            )

    return important_files