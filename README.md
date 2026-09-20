# 🏹 Repo-Parth

### **Give me a GitHub repository. I'll explain the entire codebase to you.**

Repo-Parth is an **AI-powered GitHub repository intelligence platform** that helps developers understand unfamiliar codebases faster.

Instead of spending hours jumping between files, searching for entry points, and figuring out how everything connects, Repo-Parth analyzes a repository and turns its structure and source code into an **interactive, AI-assisted understanding layer**.

> **Read less. Understand more. Build faster.**

---

## 🚀 Why Repo-Parth?

Every developer eventually faces the same problem:

**You open a GitHub repository you've never seen before.**

There are hundreds of files.

You don't know where the application starts.

You don't know which files matter.

You don't know how the components connect.

And eventually you end up asking:

> *"Okay... where do I even start?"*

Repo-Parth is built to answer that question.

It transforms a repository from a collection of files into something you can **explore, understand, and question.**

---

## ✨ What Repo-Parth Does

### 🔗 1. GitHub Repository Ingestion

Paste a public GitHub repository URL and Repo-Parth automatically retrieves:

* Repository metadata
* Default branch
* Primary language
* Repository file tree
* README content
* File sizes
* Repository structure

No manual file uploads required.

---

### 🧠 2. Repository Intelligence

Repo-Parth analyzes the repository to identify:

* Technologies used
* Important project files
* Frameworks
* Configuration files
* Backend entry points
* Frontend entry points
* Database/model files
* Routing files
* CI/CD workflows

For example, a Django repository can automatically surface:

```text
manage.py        → Django project entry point
settings.py      → Django application configuration
urls.py          → Django URL routing
models.py        → Database models
```

This gives developers an immediate starting point when entering an unfamiliar codebase.

---

### 🌳 3. Interactive File Explorer

Instead of staring at a raw GitHub repository, Repo-Parth provides an interactive file explorer.

Select a file and inspect its:

* Path
* Type
* Size
* Source code
* Project context

The explorer makes navigating an unfamiliar repository significantly more direct.

---

### 📖 4. Actual Source Code Retrieval

Repo-Parth doesn't stop at filenames.

When a developer selects a file, the platform retrieves the **actual source code from GitHub**.

This allows the AI layer to reason over real implementation details instead of relying purely on filenames or assumptions.

---

### 🤖 5. Repository-Aware AI Assistant

This is where Repo-Parth becomes more than a repository browser.

Developers can ask questions such as:

```text
How does Django start this project?

Where is authentication implemented?

How does the backend communicate with the frontend?

What does this file do?

Which files are responsible for database models?

How does this API flow work?
```

The AI receives repository metadata, project structure, important files, and selected source code as context.

It is explicitly instructed to:

* Use the provided repository context
* Reference relevant file paths
* Explain code in developer-friendly language
* Distinguish facts from inference
* Avoid inventing files or functionality
* State when the available context is insufficient

### Example

Ask:

> **How does Django start this project?**

Repo-Parth can trace the execution from:

```text
backend/manage.py
        ↓
DJANGO_SETTINGS_MODULE
        ↓
atlas_config.settings
        ↓
Django management system
        ↓
execute_from_command_line(sys.argv)
```

Instead of simply saying *"this is a Django project,"* it explains **how the actual code works.**

---

# 🏗️ Architecture

Repo-Parth follows a modular architecture designed around repository analysis and AI-assisted understanding.

```text
                         ┌─────────────────────┐
                         │      Developer      │
                         └──────────┬──────────┘
                                    │
                                    │ GitHub URL
                                    ▼
                         ┌─────────────────────┐
                         │   React Frontend    │
                         │                     │
                         │  Repository UI     │
                         │  File Explorer     │
                         │  AI Assistant      │
                         └──────────┬──────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI Backend  │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ GitHub Service │ │ File Analyzer  │ │ Tech Detector  │
        │                │ │                │ │                │
        │ Repository     │ │ Important      │ │ Frameworks &   │
        │ Metadata       │ │ Files          │ │ Technologies   │
        │ File Tree      │ │ Classification │ │                │
        │ Source Code    │ │                │ │                │
        └────────────────┘ └────────────────┘ └────────────────┘
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Repository Context  │
                         │                     │
                         │ Structure           │
                         │ Technologies        │
                         │ Important Files     │
                         │ Source Code         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Gemini AI       │
                         │                     │
                         │ Repository-aware    │
                         │ reasoning layer     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    AI Explanation   │
                         └─────────────────────┘
```

---

# 🛠️ Tech Stack

### Frontend

* **React**
* **TypeScript**
* **Vite**
* **Axios**
* **React Router**
* **Lucide React**
* **React Flow**

### Backend

* **Python**
* **FastAPI**
* **HTTPX**
* **Pydantic**
* **python-dotenv**

### AI

* **Google Gemini API**
* Repository-grounded prompting
* Source-code contextual reasoning

### Data Source

* **GitHub REST API**

---

# 🔄 How It Works

Repo-Parth follows a simple pipeline:

### 1. Paste Repository

```text
https://github.com/username/project
```

### 2. Analyze

Repo-Parth communicates with GitHub and retrieves:

```text
Repository Metadata
        +
File Tree
        +
README
```

### 3. Understand

The backend analyzes the repository to determine:

```text
Technologies
        +
Important Files
        +
Project Structure
```

### 4. Explore

The developer can navigate the repository through the interactive file explorer.

### 5. Inspect

Selecting a file retrieves its actual source code.

### 6. Ask

The developer asks Repo-Parth a question.

### 7. Explain

The AI receives the relevant repository context and generates a repository-specific explanation.

---

# 🧩 Project Structure

```text
Repo-Parth/
│
├── backend/
│   └── app/
│       ├── services/
│       │   ├── ai.py
│       │   ├── detector.py
│       │   ├── file_analyzer.py
│       │   ├── github.py
│       │   └── structure.py
│       │
│       └── main.py
│
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── App.css
│       └── ...
│
├── .gitignore
└── README.md
```

---

# ⚡ Getting Started

## Prerequisites

Make sure you have:

* Node.js
* Python 3.10+
* Git
* A Google Gemini API key

---

## 1. Clone the repository

```bash
git clone https://github.com/Lekhak666/Repo-Parth.git

cd Repo-Parth
```

---

## 2. Setup the Backend

```bash
cd backend
```

Create a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Gemini

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

---

## 4. Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 5. Start the Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Vite:

```bash
npm run dev
```

Then open the local URL shown by Vite.

---

# 🔌 API Overview

### Health Check

```http
GET /api/health
```

### Analyze Repository

```http
POST /api/repositories/analyze
```

Example:

```json
{
  "repo_url": "https://github.com/Lekhak666/Atlas"
}
```

### Retrieve File Source

```http
POST /api/repositories/file
```

Example:

```json
{
  "repo_url": "https://github.com/Lekhak666/Atlas",
  "file_path": "backend/manage.py"
}
```

### Ask Repo-Parth AI

```http
POST /api/ai/chat
```

The AI endpoint receives:

```text
Question
Repository Metadata
Technologies
Important Files
Project Structure
Source Files
```

and returns a repository-aware explanation.

---

# 🎯 The Problem We're Solving

Modern software projects are increasingly complex.

A developer joining an existing project may have to understand:

* Multiple frameworks
* Hundreds of files
* Unfamiliar architecture
* Backend/frontend interactions
* Configuration layers
* APIs
* Database models
* Authentication flows
* Deployment systems

Traditional documentation often becomes outdated.

Repo-Parth takes a different approach:

> **The repository itself becomes the source of understanding.**

Instead of relying entirely on manually maintained documentation, Repo-Parth analyzes the actual codebase and uses that context to help developers navigate it.

---

# 🧠 Design Philosophy

Repo-Parth is built around three principles:

### **1. Context over Guesswork**

The AI should answer using the repository context it actually receives.

### **2. Code over Assumptions**

The source code is more authoritative than filenames or generic framework knowledge.

### **3. Understanding over Summarization**

The goal isn't simply to summarize a repository.

The goal is to help a developer **understand how it works.**

---

# 🚧 Roadmap

Repo-Parth is actively evolving.

### Current

* [x] GitHub repository ingestion
* [x] Repository metadata extraction
* [x] Recursive file tree analysis
* [x] Technology detection
* [x] Important file detection
* [x] Project structure analysis
* [x] Interactive file explorer
* [x] Source code retrieval
* [x] Repository-aware AI assistant

### Next

* [ ] Intelligent automatic file selection for questions
* [ ] Multi-file reasoning
* [ ] Interactive architecture visualization
* [ ] Dependency relationship mapping
* [ ] Code flow visualization
* [ ] Better language/framework detection
* [ ] Repository-wide semantic search
* [ ] Improved AI context management
* [ ] Private repository support
* [ ] Authentication
* [ ] Deployment-ready production architecture

---

# 🏹 Why "Parth"?

**Parth** is an epithet associated with **Arjuna** from the Mahabharata.

For us, it represents precision:

> **Find the target. Understand the path.**

Repo-Parth applies that idea to software repositories — helping developers find the relevant code and understand the path through a complex codebase.

---

# 🔐 Security & Privacy

Repo-Parth currently focuses on **public GitHub repositories** for its MVP.

API keys and environment variables are kept outside the repository using `.env` configuration and are excluded through `.gitignore`.

Private repository support is planned for a future version with appropriate authentication and authorization mechanisms.

---

# 🤝 Contributing

Contributions, ideas, and feedback are welcome.

If you have an idea that can make repository understanding faster, clearer, or more intelligent:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Commit your changes
5. Open a Pull Request

---

# ⭐ Support the Project

If Repo-Parth helps you understand a codebase faster, consider giving the repository a ⭐.

It helps the project grow and motivates further development.

---

<div align="center">

### **🏹 Repo-Parth**

**Your GitHub repository. Understood.**

Built for developers who'd rather **build than dig through codebases.**

</div>
