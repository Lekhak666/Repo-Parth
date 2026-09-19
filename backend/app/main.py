from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Repo-Parth API",
    description="AI-powered GitHub repository intelligence platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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