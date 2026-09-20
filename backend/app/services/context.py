from pathlib import Path
import re


STOP_WORDS = {
    "how",
    "does",
    "do",
    "the",
    "this",
    "that",
    "what",
    "why",
    "where",
    "when",
    "is",
    "are",
    "a",
    "an",
    "of",
    "to",
    "in",
    "for",
    "on",
    "with",
    "and",
    "or",
    "project",
    "code",
    "work",
}


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())

    return {
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    }


def score_file(
    path: str,
    question_words: set[str],
    important_paths: set[str],
) -> int:

    normalized_path = path.lower()
    filename = Path(path).name.lower()
    path_parts = set(
        part
        for part in re.findall(r"[a-zA-Z0-9_]+", normalized_path)
        if len(part) > 2
    )

    score = 0

    # Direct word matches in the path
    for word in question_words:
        if word in path_parts:
            score += 5

        if word in filename:
            score += 8

    # Important files receive a small boost
    if path in important_paths:
        score += 3

    # Framework/configuration files are often useful
    important_names = {
        "settings.py",
        "urls.py",
        "models.py",
        "views.py",
        "routes.py",
        "api.py",
        "serializers.py",
        "services.py",
        "main.py",
        "app.py",
        "manage.py",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
    }

    if filename in important_names:
        score += 2

    # Question-specific concepts
    concept_keywords = {
        "auth": {
            "authentication",
            "authenticate",
            "authorization",
            "login",
            "logout",
            "permission",
            "permissions",
            "token",
            "jwt",
            "session",
            "user",
            "users",
        },
        "database": {
            "database",
            "db",
            "model",
            "models",
            "migration",
            "query",
            "postgres",
            "mysql",
            "sqlite",
        },
        "api": {
            "api",
            "endpoint",
            "request",
            "response",
            "route",
            "routes",
            "http",
        },
        "frontend": {
            "frontend",
            "react",
            "component",
            "page",
            "ui",
            "interface",
        },
        "deployment": {
            "deploy",
            "deployment",
            "docker",
            "production",
            "server",
            "hosting",
        },
    }

    for keywords in concept_keywords.values():
        if question_words.intersection(keywords):
            if path_parts.intersection(keywords):
                score += 6

    return score


def select_relevant_files(
    question: str,
    files: list[dict],
    important_files: list[dict],
    max_files: int = 8,
) -> list[str]:

    question_words = tokenize(question)

    important_paths = {
        file["path"]
        for file in important_files
        if file.get("path")
    }

    scored_files = []

    for file in files:
        path = file.get("path")

        if not path:
            continue

        # Only actual files, not directories
        if file.get("type") != "blob":
            continue

        score = score_file(
            path,
            question_words,
            important_paths,
        )

        scored_files.append((score, path))

    scored_files.sort(
        key=lambda item: (-item[0], item[1])
    )

    selected = [
        path
        for score, path in scored_files
        if score > 0
    ][:max_files]

    # Always provide some important files if the question
    # produced weak matches.
    if len(selected) < 3:
        for path in important_paths:
            if path not in selected:
                selected.append(path)

            if len(selected) >= 3:
                break

    return selected[:max_files]