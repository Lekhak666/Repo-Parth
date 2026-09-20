import os
from pathlib import Path

from app.services.context import select_relevant_files
from app.services.github import fetch_file_content
from dotenv import load_dotenv
from fastapi import HTTPException
from groq import AsyncGroq

from .relationships import detect_relationships


# ai.py -> services -> app -> backend -> Repo-Parth
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

MAX_CHARS_PER_FILE = 12000

# Phase 5B:
# Maximum number of extra files fetched because they are
# connected to already retrieved files.
MAX_RELATION_FILES = 4


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured.",
        )

    return AsyncGroq(api_key=api_key)


def build_source_context(
    source_files: list[dict],
) -> str:

    parts = []

    for file in source_files:

        path = file.get(
            "path",
            "UNKNOWN FILE",
        )

        content = (
            file.get("content") or ""
        )[:MAX_CHARS_PER_FILE]

        parts.append(
            f"=== FILE: {path} ===\n"
            f"{content}\n"
            f"=== END FILE ===\n"
        )

    return "\n".join(parts)


def build_relationship_context(
    relationships: list[dict],
) -> str:

    if not relationships:
        return (
            "No direct file relationships were "
            "detected among the retrieved source files."
        )

    parts = []

    for relationship in relationships:

        source = relationship.get(
            "source",
            "UNKNOWN",
        )

        target = relationship.get(
            "target",
            "UNKNOWN",
        )

        relation_type = relationship.get(
            "type",
            "related",
        )

        import_name = relationship.get(
            "import",
        )

        line = (
            f"- {source} "
            f"--{relation_type}--> "
            f"{target}"
        )

        if import_name:
            line += (
                f" "
                f"(import: {import_name})"
            )

        parts.append(line)

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

    # =========================================================
    # 1. SELECT RELEVANT FILES
    # =========================================================

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

    # =========================================================
    # 2. START WITH FILES PROVIDED BY FRONTEND
    # =========================================================

    all_source_files = list(
        source_files or []
    )

    existing_paths = {
        file.get("path")
        for file in all_source_files
        if file.get("path")
    }

    print(
        "\nSOURCE FILES ALREADY PROVIDED "
        "BY FRONTEND:"
    )

    if existing_paths:

        for path in existing_paths:
            print(f"  ✓ {path}")

    else:
        print("  (none)")

    # =========================================================
    # 3. FETCH RELEVANT FILES
    # =========================================================

    print(
        "\nFETCHING RELEVANT FILES FROM GITHUB:"
    )

    for path in relevant_paths:

        if path in existing_paths:

            print(
                f"  ↪ Already available: {path}"
            )

            continue

        try:

            print(
                f"  → Fetching: {path}"
            )

            file_data = await fetch_file_content(
                repo_url,
                path,
            )

            if not file_data:

                print(
                    f"  ✗ Empty response: {path}"
                )

                continue

            content = file_data.get(
                "content"
            )

            if not content:

                print(
                    f"  ✗ No source content "
                    f"returned: {path}"
                )

                continue

            all_source_files.append(
                file_data
            )

            existing_paths.add(path)

            print(
                f"  ✓ Fetched: {path} "
                f"({len(content)} characters)"
            )

        except Exception as exc:

            print(
                f"  ✗ Could not fetch "
                f"{path}: {exc}"
            )

    # =========================================================
    # 4. DETECT RELATIONSHIPS
    # =========================================================
    #
    # IMPORTANT:
    #
    # detect_relationships() accepts ONLY source_files.
    #
    # It builds its own index from the files whose actual
    # source code we have successfully retrieved.
    #
    # =========================================================

    relationships = detect_relationships(
        source_files=all_source_files,
    )

    print(
        "\nFILE RELATIONSHIPS DETECTED:"
    )

    if relationships:

        for relationship in relationships:

            source = relationship.get(
                "source",
                "UNKNOWN",
            )

            target = relationship.get(
                "target",
                "UNKNOWN",
            )

            relation_type = relationship.get(
                "type",
                "related",
            )

            print(
                f"  ↳ {source} "
                f"--{relation_type}--> "
                f"{target}"
            )

    else:

        print("  (none)")

    # =========================================================
    # 5. RELATIONSHIP-AWARE RETRIEVAL
    # =========================================================
    #
    # If a retrieved file imports another file that we already
    # have source code for, the relationship is known.
    #
    # We also attempt to fetch a limited number of related
    # repository files from the repository metadata.
    #
    # Since the detector can only resolve relationships among
    # retrieved source files, we use relationship targets as
    # hints and then re-run the detector after fetching them.
    #
    # =========================================================

    related_paths = []

    repository_path_set = {
        file.get("path")
        for file in repository_files
        if file.get("path")
    }

    for relationship in relationships:

        source = relationship.get(
            "source"
        )

        target = relationship.get(
            "target"
        )

        if not source or not target:
            continue

        if source not in existing_paths:
            continue

        if target in existing_paths:
            continue

        if target not in repository_path_set:
            continue

        if target not in related_paths:
            related_paths.append(target)

    related_paths = related_paths[
        :MAX_RELATION_FILES
    ]

    if related_paths:

        print(
            "\nFETCHING RELATED FILES:"
        )

        for path in related_paths:

            try:

                print(
                    f"  → Relationship fetch: "
                    f"{path}"
                )

                file_data = await fetch_file_content(
                    repo_url,
                    path,
                )

                if not file_data:

                    print(
                        f"  ✗ Empty response: "
                        f"{path}"
                    )

                    continue

                content = file_data.get(
                    "content"
                )

                if not content:

                    print(
                        f"  ✗ No source content "
                        f"returned: {path}"
                    )

                    continue

                all_source_files.append(
                    file_data
                )

                existing_paths.add(path)

                print(
                    f"  ✓ Relationship file "
                    f"fetched: {path} "
                    f"({len(content)} characters)"
                )

            except Exception as exc:

                print(
                    f"  ✗ Could not fetch "
                    f"related file {path}: {exc}"
                )

    else:

        print(
            "\nNO ADDITIONAL RELATED FILES "
            "REQUIRED."
        )

    # =========================================================
    # 6. RE-RUN RELATIONSHIP DETECTION
    # =========================================================
    #
    # Newly fetched files are now part of the detector's
    # source index.
    #
    # =========================================================

    relationships = detect_relationships(
        source_files=all_source_files,
    )

    relationship_context = (
        build_relationship_context(
            relationships
        )
    )

    # =========================================================
    # 7. BUILD SOURCE CONTEXT
    # =========================================================

    source_context = build_source_context(
        all_source_files
    )

    print(
        "\nSOURCE FILES ACTUALLY SENT TO GROQ:"
    )

    if all_source_files:

        for file in all_source_files:

            path = file.get(
                "path",
                "UNKNOWN",
            )

            content_length = len(
                file.get("content") or ""
            )

            print(
                f"  ✓ {path} "
                f"({content_length} characters)"
            )

    else:

        print("  (NONE)")

    print(
        "\nFINAL RELATIONSHIP MAP:"
    )

    if relationships:

        for relationship in relationships:

            source = relationship.get(
                "source",
                "UNKNOWN",
            )

            target = relationship.get(
                "target",
                "UNKNOWN",
            )

            relation_type = relationship.get(
                "type",
                "related",
            )

            print(
                f"  ✓ {source} "
                f"--{relation_type}--> "
                f"{target}"
            )

    else:

        print("  (NONE)")

    print("=" * 70 + "\n")

    # =========================================================
    # 8. BUILD CONTEXT STRINGS
    # =========================================================

    tech_list = ", ".join(
        technologies
    )

    selected_context = "\n".join(
        f"- {path}"
        for path in relevant_paths
    )

    # =========================================================
    # 9. REPOSITORY-AWARE PROMPT
    # =========================================================

    prompt = f"""
You are Repo-Parth, an AI-powered GitHub repository
intelligence assistant.

Your job is to help a developer understand THIS repository
using ONLY the repository information, detected file
relationships, and actual source code provided below.

============================================================
STRICT SOURCE-GROUNDING RULES
============================================================

1. You may ONLY make repository-specific claims that are
directly supported by information explicitly provided in this
prompt.

2. SOURCE CODE is the strongest evidence.

3. FILE RELATIONSHIPS are structural evidence showing
detected relationships such as imports between files.

4. NEVER assume that a file exists because it is common in
Django, React, FastAPI, Python, JavaScript, TypeScript, or
any other framework.

5. NEVER describe the contents of a file unless its actual
contents appear under SOURCE CODE.

6. A file appearing under RELEVANT FILES SELECTED FOR THIS
QUESTION does NOT mean its contents were successfully fetched.

7. A file appearing under PROJECT STRUCTURE does NOT mean
its contents were provided.

8. A file appearing under IMPORTANT FILES does NOT mean
its contents were provided.

9. You may ONLY claim that a file was used as source evidence
if that file appears under SOURCE CODE.

10. When mentioning a repository file path, ONLY mention paths
that actually appear somewhere in the supplied repository
context.

11. NEVER invent paths such as:

    apps/accounts/views.py
    apps/accounts/models.py
    settings.py
    urls.py

unless that exact path is actually present in the supplied
repository context.

12. Do NOT use generic framework conventions as evidence about
this repository.

13. If the source context is insufficient, say:

"I don't have enough source context to answer that reliably."

Then explain exactly what information is missing.

14. Clearly distinguish:

FACT:
Information directly visible in the provided repository
context.

INFERENCE:
A reasonable interpretation based on visible evidence.

UNKNOWN:
Information that is not available in the provided context.

15. NEVER invent:

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

16. If a source file was selected but could not be fetched,
treat its contents as UNKNOWN.

17. If a file is referenced by another source file but its
contents are not included, you may mention the referenced
module/path only if that reference actually appears in the
provided source code.

18. Do not convert Python module names into assumed file paths
unless the exact path is present in the repository context.

19. When asked "What files did you use?", list ONLY files whose
actual source code appears under SOURCE CODE.

20. Do not claim that a file was used merely because it was
selected for retrieval.

21. If there is a conflict between your general programming
knowledge and the supplied repository source code, trust the
supplied repository source code.

============================================================
FILE RELATIONSHIP MAP
============================================================

The following relationships were detected from the actual
retrieved source files.

Treat these as STRUCTURAL EVIDENCE.

For example:

A --imports--> B

means that the repository source supports that A imports or
references B according to the relationship detector.

DO NOT treat an import relationship as proof of a complete
runtime execution flow.

DO NOT invent relationships that are not listed here.

You may combine multiple documented relationships into a
dependency chain when the individual links are present.

{relationship_context}

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

Use the FILE RELATIONSHIP MAP when explaining how files
connect.

When explaining a multi-file flow, explicitly show the
supported chain when possible.

For example:

file A
  ↓ imports
file B
  ↓ imports
file C

Only show a chain when each relationship is supported by the
FILE RELATIONSHIP MAP or source code.

RELATIONSHIP CHAIN RULE:

When tracing relationships between files, NEVER create a
sequential chain merely because multiple files appear in the
relationship map.

A chain such as:

A → B → C

is valid ONLY when the relationship map explicitly contains:

A → B
B → C

If the relationships are independent, present them as separate
connections instead.

For example, if the relationship map contains:

A → B
C → D
E → B

do NOT present this as:

A → B → C → D → E

Instead, describe the independent relationships separately.

Distinguish between:

1. DIRECT CONNECTION
   One file directly imports another.

2. MULTI-HOP CONNECTION
   A valid chain exists because each consecutive relationship
   is explicitly supported.

3. SHARED DEPENDENCY
   Multiple files import the same target.

4. APP / MODULE ASSOCIATION
   Files belong to the same application or module but are not
   necessarily directly connected by imports.

Do NOT describe an app/module association as an import chain.

Do not fill missing repository information with framework
conventions.

If there is insufficient evidence, explicitly say so.

When useful, structure the answer as:

FACT
- Directly supported by source or relationship evidence.

INFERENCE
- Reasonable interpretation based on the supplied evidence.

UNKNOWN
- Information that cannot be determined from the supplied
source context.

If the user asks which files were used, list only files whose
actual source code appears in SOURCE CODE.

If the user asks how files relate to one another, explain the
relationship using the detected FILE RELATIONSHIP MAP first,
then use the actual source code to explain what that
relationship does.
"""

    # =========================================================
    # 10. ASK GROQ
    # =========================================================

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

            "relationships": relationships,
        }

    except Exception as exc:

        print(
            f"Groq error: {exc}"
        )

        error_text = str(exc)

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Groq rate limit or quota was reached. "
                    "Please try again shortly."
                ),
            ) from exc

        if (
            "401" in error_text
            or "authentication"
            in error_text.lower()
        ):

            raise HTTPException(
                status_code=401,
                detail=(
                    "Groq authentication failed. "
                    "Check your GROQ_API_KEY."
                ),
            ) from exc

        raise HTTPException(
            status_code=500,
            detail=(
                "Repo-Parth AI encountered an unexpected "
                "Groq error."
            ),
        ) from exc