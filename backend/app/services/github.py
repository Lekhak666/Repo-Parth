import os
import re

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from app.services.detector import detect_technologies
from app.services.file_analyzer import find_important_files
from app.services.structure import build_project_structure


# Load the root .env file
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
load_dotenv(os.path.join(BASE_DIR, ".env"))


GITHUB_API = "https://api.github.com"


HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}


# Optional GitHub authentication.
#
# If GITHUB_TOKEN exists, GitHub gives us a much higher API rate limit.
# If it does not exist, Repo-Parth still works with unauthenticated access
# until GitHub's public rate limit is reached.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def parse_github_url(repo_url: str) -> tuple[str, str]:
    pattern = r"github\.com/([^/]+)/([^/#?]+)"
    match = re.search(pattern, repo_url)

    if not match:
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid GitHub repository URL.",
        )

    owner = match.group(1)
    repo = match.group(2).removesuffix(".git")

    return owner, repo


def raise_github_error(response: httpx.Response) -> None:
    """
    Convert common GitHub API errors into useful FastAPI errors.
    """

    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="GitHub authentication failed. Please check GITHUB_TOKEN.",
        )

    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining")

        raise HTTPException(
            status_code=429,
            detail=(
                "GitHub API rate limit exceeded. "
                f"Remaining requests: {remaining or 'unknown'}. "
                "Add a valid GITHUB_TOKEN to the root .env file."
            ),
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="GitHub repository or file not found.",
        )

    response.raise_for_status()


async def analyze_repository(repo_url: str) -> dict:
    owner, repo = parse_github_url(repo_url)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=20.0,
        follow_redirects=True,
    ) as client:

        # ---------------------------------------------------------
        # 1. Repository metadata
        # ---------------------------------------------------------

        repo_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}"
        )

        raise_github_error(repo_response)

        repository = repo_response.json()

        # ---------------------------------------------------------
        # 2. Repository tree
        # ---------------------------------------------------------

        default_branch = repository["default_branch"]

        tree_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": "true"},
        )

        raise_github_error(tree_response)

        tree_data = tree_response.json()

        # ---------------------------------------------------------
        # 3. README
        # ---------------------------------------------------------

        readme_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/readme"
        )

        readme = ""

        if readme_response.status_code == 200:
            readme_data = readme_response.json()

            download_url = readme_data.get("download_url")

            if download_url:
                raw_readme = await client.get(download_url)

                if raw_readme.status_code == 200:
                    readme = raw_readme.text

        # ---------------------------------------------------------
        # 4. Build repository file list
        # ---------------------------------------------------------

        files = [
            {
                "path": item["path"],
                "type": item["type"],
                "size": item.get("size"),
            }
            for item in tree_data.get("tree", [])
        ]

        # ---------------------------------------------------------
        # 5. Analyze repository
        # ---------------------------------------------------------

        technologies = detect_technologies(files)

        important_files = find_important_files(files)

        project_structure = build_project_structure(files)

        # ---------------------------------------------------------
        # 6. Return repository analysis
        # ---------------------------------------------------------

        return {
            "repository": {
                "name": repository["name"],
                "full_name": repository["full_name"],
                "description": repository["description"],
                "html_url": repository["html_url"],
                "default_branch": default_branch,
                "language": repository["language"],
                "stars": repository["stargazers_count"],
                "forks": repository["forks_count"],
            },
            "files": files,
            "file_count": len(files),
            "readme": readme,
            "tree_truncated": tree_data.get("truncated", False),
            "technologies": technologies,
            "important_files": important_files,
            "project_structure": project_structure,
        }


async def fetch_file_content(
    repo_url: str,
    file_path: str,
) -> dict:
    owner, repo = parse_github_url(repo_url)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=20.0,
        follow_redirects=True,
    ) as client:

        # ---------------------------------------------------------
        # 1. Get repository metadata
        # ---------------------------------------------------------

        repo_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}"
        )

        raise_github_error(repo_response)

        repository = repo_response.json()

        default_branch = repository["default_branch"]

        # ---------------------------------------------------------
        # 2. Fetch file metadata
        # ---------------------------------------------------------

        file_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/contents/{file_path}",
            params={"ref": default_branch},
        )

        raise_github_error(file_response)

        file_data = file_response.json()

        # ---------------------------------------------------------
        # 3. Make sure it is actually a file
        # ---------------------------------------------------------

        if file_data.get("type") != "file":
            raise HTTPException(
                status_code=400,
                detail="The selected path is not a file.",
            )

        # ---------------------------------------------------------
        # 4. Get raw file URL
        # ---------------------------------------------------------

        download_url = file_data.get("download_url")

        if not download_url:
            raise HTTPException(
                status_code=400,
                detail="Unable to retrieve the file contents.",
            )

        # ---------------------------------------------------------
        # 5. Download actual source code
        # ---------------------------------------------------------

        raw_headers = {}

        if GITHUB_TOKEN:
            raw_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        raw_response = await client.get(
            download_url,
            headers=raw_headers,
        )

        if raw_response.status_code == 403:
            raise HTTPException(
                status_code=429,
                detail="GitHub rate limit exceeded while downloading file.",
            )

        raw_response.raise_for_status()

        # ---------------------------------------------------------
        # 6. Return source file
        # ---------------------------------------------------------

        return {
            "path": file_path,
            "content": raw_response.text,
            "size": file_data.get("size"),
            "type": file_data.get("type"),
        }
