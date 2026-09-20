import re

import httpx
from fastapi import HTTPException

from app.services.detector import detect_technologies
from app.services.file_analyzer import find_important_files
from app.services.structure import build_project_structure

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}


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


async def analyze_repository(repo_url: str) -> dict:
    owner, repo = parse_github_url(repo_url)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=20.0,
    ) as client:

        # 1. Repository metadata
        repo_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}"
        )

        if repo_response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="GitHub repository not found.",
            )

        repo_response.raise_for_status()
        repository = repo_response.json()

        # 2. Repository tree
        default_branch = repository["default_branch"]

        tree_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": "true"},
        )

        tree_response.raise_for_status()
        tree_data = tree_response.json()

        # 3. README
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

        files = [
            {
                "path": item["path"],
                "type": item["type"],
                "size": item.get("size"),
            }
            for item in tree_data.get("tree", [])
        ]

        technologies = detect_technologies(files)
        important_files = find_important_files(files)
        project_structure = build_project_structure(files)

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
    ) as client:

        # Get repository metadata so we know the default branch
        repo_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}"
        )

        if repo_response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="GitHub repository not found.",
            )

        repo_response.raise_for_status()
        repository = repo_response.json()

        default_branch = repository["default_branch"]

        # Fetch the file from GitHub
        file_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/contents/{file_path}",
            params={"ref": default_branch},
        )

        if file_response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="File not found in the repository.",
            )

        file_response.raise_for_status()

        file_data = file_response.json()

        # Make sure the selected path is actually a file
        if file_data.get("type") != "file":
            raise HTTPException(
                status_code=400,
                detail="The selected path is not a file.",
            )

        download_url = file_data.get("download_url")

        if not download_url:
            raise HTTPException(
                status_code=400,
                detail="Unable to retrieve the file contents.",
            )

        raw_response = await client.get(download_url)

        raw_response.raise_for_status()

        return {
            "path": file_path,
            "content": raw_response.text,
            "size": file_data.get("size"),
            "type": file_data.get("type"),
        }