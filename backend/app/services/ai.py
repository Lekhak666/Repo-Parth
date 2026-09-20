import os
from pathlib import Path

from app.services.context import select_relevant_files
from app.services.github import fetch_file_content
from dotenv import load_dotenv
from fastapi import HTTPException
from groq import AsyncGroq


# ai.py -> services -> app -> backend -> Repo-Parth
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_CHARS_PER_FILE = 12000


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured.",
        )

    return AsyncGroq(api_key=api_key)


def build_source_context(source_files: list[dict]) -> str:
    parts = []

    for file in source_files:
        path = file.get("path", "UNKNOWN FILE")
        content = (file.get("content") or "")[:MAX_CHARS_PER_FILE]

        parts.append(
            f"=== FILE: {path} ===\n"
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
    repository_files: list[dict],
    repo_url: str,
) -> dict:

    client = get_groq_client()

    # ---------------------------------------------------------
    # 1. Select files relevant to the user's question
    # ---------------------------------------------------------

    relevant_paths = select_relevant_files(
        question=question,
        files=repository_files,
        important_files=important_files,
        max_files=8,
    )

    print("\n" + "=" * 70)
    print("REPO-PARTH CONTEXT DEBUG")
    print("=" * 70)

    print("\nQUESTION:")
    print(question)

    print("\nRELEVANT FILES SELECTED:")
    if relevant_paths:
        for path in relevant_paths:
            print(f"  ✓ {path}")
    else:
        print("  (none)")

    # ---------------------------------------------------------
    # 2. Start with source files already supplied by frontend
    # ---------------------------------------------------------

    all_source_files = list(source_files or [])

    existing_paths = {
        file.get("path")
        for file in all_source_files
        if file.get("path")
    }

    print("\nSOURCE FILES ALREADY PROVIDED BY FRONTEND:")
    if existing_paths:
        for path in existing_paths:
            print(f"  ✓ {path}")
    else:
        print("  (none)")

    # ---------------------------------------------------------
    # 3. Fetch automatically selected files from GitHub
    # ---------------------------------------------------------

    print("\nFETCHING RELEVANT FILES FROM GITHUB:")

    for path in relevant_paths:

        if path in existing_paths:
            print(f"  ↪ Already available: {path}")
            continue

        try:
            print(f"  → Fetching: {path}")

            file_data = await fetch_file_content(
                repo_url,
                path,
            )

            if not file_data:
                print(f"  ✗ Empty response: {path}")
                continue

            content = file_data.get("content")

            if not content:
                print(f"  ✗ No source content returned: {path}")
                continue

            all_source_files.append(file_data)
            existing_paths.add(path)

            print(
                f"  ✓ Fetched: {path} "
                f"({len(content)} characters)"
            )

        except Exception as exc:
            print(
                f"  ✗ Could not fetch {path}: {exc}"
            )

    # ---------------------------------------------------------
    # 4. Build source context
    # ---------------------------------------------------------

    source_context = build_source_context(
        all_source_files
    )

    print("\nSOURCE FILES ACTUALLY SENT TO GROQ:")

    if all_source_files:
        for file in all_source_files:
            path = file.get("path", "UNKNOWN")
            content_length = len(
                file.get("content") or ""
            )

            print(
                f"  ✓ {path} "
                f"({content_length} characters)"
            )
    else:
        print("  (NONE)")

    print("=" * 70 + "\n")

    tech_list = ", ".join(technologies)

    selected_context = "\n".join(
        f"- {path}"
        for path in relevant_paths
    )

    # ---------------------------------------------------------
    # 5. Build repository-aware prompt
    # ---------------------------------------------------------

    prompt = f"""
You are Repo-Parth, an AI-powered GitHub repository
intelligence assistant.

Your job is to help a developer understand THIS repository
using ONLY the repository information and actual source code
provided below.

============================================================
STRICT SOURCE-GROUNDING RULES
============================================================

1. You may ONLY make repository-specific claims that are
directly supported by information explicitly provided in this
prompt.

2. SOURCE CODE is the strongest evidence.

3. NEVER assume that a file exists because it is common in
Django, React, FastAPI, Python, JavaScript, TypeScript, or
any other framework.

4. NEVER describe the contents of a file unless its actual
contents appear under SOURCE CODE.

5. A file appearing under RELEVANT FILES SELECTED FOR THIS
QUESTION does NOT mean its contents were successfully fetched.

6. A file appearing under PROJECT STRUCTURE does NOT mean
its contents were provided.

7. A file appearing under IMPORTANT FILES does NOT mean
its contents were provided.

8. You may ONLY claim that a file was used as source evidence
if that file appears under SOURCE CODE.

9. When mentioning a repository file path, ONLY mention paths
that actually appear somewhere in the supplied repository
context.

10. NEVER invent paths such as:
    apps/accounts/views.py
    apps/accounts/models.py
    settings.py
    urls.py

unless that exact path is actually present in the supplied
repository context.

11. Do NOT use generic framework conventions as evidence about
this repository.

12. If the source context is insufficient, say:

"I don't have enough source context to answer that reliably."

Then explain exactly what information is missing.

13. Clearly distinguish:

FACT:
Information directly visible in the provided repository
context.

INFERENCE:
A reasonable interpretation based on visible evidence.

UNKNOWN:
Information that is not available in the provided context.

14. NEVER invent:

- functions
- classes
- routes
- settings
- imports
- applications
- dependencies
- database configuration
- authentication mechanisms
- API endpoints
- configuration values
- file contents

15. If a source file was selected but could not be fetched,
treat its contents as UNKNOWN.

16. If a file is referenced by another source file but its
contents are not included, you may mention the referenced
module/path only if that reference actually appears in the
provided source code.

17. Do not convert Python module names into assumed file paths
unless the exact path is present in the repository context.

18. When asked "What files did you use?", list ONLY files whose
actual source code appears under SOURCE CODE.

19. Do not claim that a file was used merely because it was
selected for retrieval.

20. If there is a conflict between your general programming
knowledge and the supplied repository source code, trust the
supplied repository source code.

============================================================
REPOSITORY
============================================================

Name:
{repository.get("name")}

Full name:
{repository.get("full_name")}

Description:
{repository.get("description")}

Default branch:
{repository.get("default_branch")}

Primary language:
{repository.get("language")}

============================================================
TECHNOLOGIES
============================================================

{tech_list}

============================================================
IMPORTANT FILES
============================================================

{important_files}

============================================================
PROJECT STRUCTURE
============================================================

{project_structure}

============================================================
RELEVANT FILES SELECTED FOR THIS QUESTION
============================================================

{selected_context}

IMPORTANT:
The files above are merely candidates selected by Repo-Parth.
Their presence here does NOT prove that their source code was
successfully retrieved.

============================================================
SOURCE CODE
============================================================

{source_context}

IMPORTANT:
ONLY files appearing in this SOURCE CODE section may be treated
as having their actual implementation available.

============================================================
USER QUESTION
============================================================

{question}

============================================================
ANSWER REQUIREMENTS
============================================================

Answer the user's question specifically about this repository.

Use actual source code whenever possible.

Do not fill missing repository information with framework
conventions.

If there is insufficient evidence, explicitly say so.

When useful, structure the answer as:

FACT
- Directly supported by source.

INFERENCE
- Reasonable interpretation based on the source.

UNKNOWN
- Information that cannot be determined from the supplied
  source context.

If the user asks which files were used, list only files whose
actual source code appears in SOURCE CODE.
"""

    # ---------------------------------------------------------
    # 6. Ask Groq
    # ---------------------------------------------------------

    try:
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.1,
        )

        answer = (
            response.choices[0].message.content
            or "I couldn't generate an explanation."
        )

        return {
            "answer": answer,
            "sources": [
                file.get("path")
                for file in all_source_files
                if file.get("path")
            ],
        }

    except Exception as exc:
        print(f"Groq error: {exc}")

        error_text = str(exc)

        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Groq rate limit or quota was reached. "
                    "Please try again shortly."
                ),
            ) from exc

        if "401" in error_text or "authentication" in error_text.lower():
            raise HTTPException(
                status_code=401,
                detail=(
                    "Groq authentication failed. "
                    "Check your GROQ_API_KEY."
                ),
            ) from exc

        raise HTTPException(
            status_code=500,
            detail="Repo-Parth AI encountered an unexpected Groq error.",
        ) from exc