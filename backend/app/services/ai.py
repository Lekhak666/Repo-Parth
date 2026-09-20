import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types

# ai.py -> services -> app -> backend -> Repo-Parth (project root)
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_CHARS_PER_FILE = 12000


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured.",
        )

    return genai.Client(api_key=api_key)


def build_source_context(source_files: list[dict]) -> str:
    parts = []

    for file in source_files:
        content = (file.get("content") or "")[:MAX_CHARS_PER_FILE]
        parts.append(
            f"=== FILE: {file['path']} ===\n"
            f"{content}\n"
            f"=== END FILE ===\n"
        )

    return "\n".join(parts)


async def ask_repo_ai(
    question: str,
    repository: dict,
    technologies: list[str],
    important_files: list[dict],
    project_structure: dict,
    source_files: list[dict],
) -> str:
    client = get_gemini_client()

    source_context = build_source_context(source_files)
    tech_list = ", ".join(technologies)

    prompt = f"""
You are Repo-Parth, an AI-powered GitHub repository
intelligence assistant.

Your job is to help a developer understand the repository
using the actual repository information and source code
provided below.

Do NOT pretend you have access to files that are not included
in the context.

If the provided context is insufficient to answer the question,
say that clearly and explain what additional file or information
would be needed.

When possible:
- Mention the relevant file paths.
- Explain the code in simple developer-friendly language.
- Describe how components connect.
- Distinguish facts visible in the code from reasonable inference.
- Do not invent functions, files, APIs, or behavior.

REPOSITORY
Name: {repository.get("name")}
Full name: {repository.get("full_name")}
Description: {repository.get("description")}
Default branch: {repository.get("default_branch")}
Primary language: {repository.get("language")}

TECHNOLOGIES
{tech_list}

IMPORTANT FILES
{important_files}

PROJECT STRUCTURE
{project_structure}

SOURCE CODE
{source_context}

USER QUESTION
{question}

Answer the user's question specifically about this repository.
"""

    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
            ),
        )
        return response.text or "I couldn't generate an explanation."

    except Exception as exc:
        print(f"Gemini error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc