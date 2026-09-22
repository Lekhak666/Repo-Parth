from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from app.services.ai import ask_repo_ai
from app.services.github import (
    analyze_repository,
    fetch_file_content,
)


app = FastAPI(
    title="Repo-Parth API",
    description="AI-powered GitHub repository intelligence platform",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://repo-parth.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RepositoryRequest(BaseModel):
    repo_url: HttpUrl


class FileContentRequest(BaseModel):
    repo_url: HttpUrl
    file_path: str


class ChatRequest(BaseModel):
    question: str
    repository: dict
    technologies: list[str]
    important_files: list[dict]
    project_structure: dict
    source_files: list[dict]
    repository_files: list[dict]
    repo_url: HttpUrl


@app.post("/api/ai/chat")
async def chat_with_repository(request: ChatRequest):
    return await ask_repo_ai(
        question=request.question,
        repository=request.repository,
        technologies=request.technologies,
        important_files=request.important_files,
        project_structure=request.project_structure,
        source_files=request.source_files,
        repository_files=request.repository_files,
        repo_url=str(request.repo_url),
    )


@app.get("/")
def root():
    return {
        "message": "Repo-Parth API is alive 🏹",
        "status": "ok",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "repo-parth-backend",
    }


@app.post("/api/repositories/analyze")
async def analyze_repository_endpoint(
    request: RepositoryRequest,
):
    return await analyze_repository(
        str(request.repo_url)
    )


@app.post("/api/repositories/file")
async def get_file_content_endpoint(
    request: FileContentRequest,
):
    return await fetch_file_content(
        str(request.repo_url),
        request.file_path,
    )