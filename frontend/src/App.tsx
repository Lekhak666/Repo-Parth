import { useMemo, useState } from "react";
import axios from "axios";

import {
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  FileCode2,
  FolderOpen,
  GitBranch,
  Loader2,
  Send,
  Sparkles,
} from "lucide-react";

import Logo from "./assets/repo-parth-logo.png";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

interface Repository {
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  default_branch: string;
  language: string | null;
  stars: number;
  forks: number;
}

interface RepositoryFile {
  path: string;
  type: string;
  size: number | null;
}

interface ImportantFile {
  path: string;
  role: string;
  size: number | null;
}

interface AnalysisResult {
  repository: Repository;
  technologies: string[];
  important_files: ImportantFile[];
  project_structure: Record<string, string[]>;
  files: RepositoryFile[];
  file_count: number;
  readme: string;
  tree_truncated: boolean;
}

interface FileRelationship {
  source: string;
  target: string;
  type: string;
  import?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  relationships?: FileRelationship[];
}

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [analysis, setAnalysis] =
    useState<AnalysisResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [selectedFile, setSelectedFile] =
    useState<RepositoryFile | null>(null);

  const [fileContent, setFileContent] = useState("");
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState("");

  const [chatQuestion, setChatQuestion] = useState("");
  const [chatMessages, setChatMessages] =
    useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  /* =========================================================
     FILE TREE
  ========================================================= */

  const fileTree = useMemo(() => {
    if (!analysis) {
      return {};
    }

    const tree: Record<string, string[]> = {};

    analysis.files.forEach((file) => {
      const parts = file.path.split("/");

      // Root-level files
      if (parts.length === 1) {
        if (!tree.root) {
          tree.root = [];
        }

        tree.root.push(file.path);
        return;
      }

      // Top-level folders
      const folder = parts[0];

      if (!tree[folder]) {
        tree[folder] = [];
      }

      tree[folder].push(file.path);
    });

    return tree;
  }, [analysis]);

  /* =========================================================
     FILE SELECTION + FETCHING
  ========================================================= */

  const selectFile = async (file: RepositoryFile) => {
    setSelectedFile(file);
    setFileContent("");
    setFileError("");
    setFileLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/api/repositories/file`,
        {
          repo_url: repoUrl,
          file_path: file.path,
        }
      );

      setFileContent(response.data.content);
    } catch (error) {
      console.error("File loading error:", error);
      setFileError("Unable to load this file.");
    } finally {
      setFileLoading(false);
    }
  };

 
  /* =========================================================
     RETURN TO REPOSITORY OVERVIEW
  ========================================================= */

  const clearSelectedFile = () => {
    setSelectedFile(null);
    setFileContent("");
    setFileError("");
    setFileLoading(false);
  };

  /* =========================================================
     ASK PARTH AI
  ========================================================= */

  const askRepoParth = async () => {
    if (
      !chatQuestion.trim() ||
      !analysis ||
      chatLoading
    ) {
      return;
    }

    const question = chatQuestion.trim();

    setChatQuestion("");
    setChatError("");

    // Add user's question immediately
    setChatMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: question,
      },
    ]);

    setChatLoading(true);

    try {
      /*
       * If the user currently has a file open,
       * send that source code to Parth as additional context.
       */
      const sourceFiles =
        selectedFile && fileContent
          ? [
              {
                path: selectedFile.path,
                content: fileContent,
                size: selectedFile.size,
                type: selectedFile.type,
              },
            ]
          : [];

      const response = await axios.post(
        `${API_URL}/api/ai/chat`,
        {
          question,
          repository: analysis.repository,
          technologies: analysis.technologies,
          important_files: analysis.important_files,
          project_structure: analysis.project_structure,
          source_files: sourceFiles,
          repository_files: analysis.files,
          repo_url: repoUrl,
        }
      );

      setChatMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: response.data.answer,
          sources: response.data.sources || [],
          relationships:
            response.data.relationships || [],
        },
      ]);
    } catch (error) {
      console.error("AI chat error:", error);

      setChatError(
        "Unable to get a response from Repo-Parth. Make sure the backend is running."
      );
    } finally {
      setChatLoading(false);
    }
  };

  /* =========================================================
     REPOSITORY ANALYSIS
  ========================================================= */

  const analyzeRepository = async () => {
    if (!repoUrl.trim()) {
      setError(
        "Please enter a GitHub repository URL."
      );
      return;
    }

    setLoading(true);
    setError("");

    setAnalysis(null);

    setSelectedFile(null);
    setFileContent("");
    setFileError("");

    setChatMessages([]);
    setChatQuestion("");
    setChatError("");

    try {
      const response =
        await axios.post<AnalysisResult>(
          `${API_URL}/api/repositories/analyze`,
          {
            repo_url: repoUrl.trim(),
          }
        );

      setAnalysis(response.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(
          err.response?.data?.detail ||
            "Unable to analyze this repository."
        );
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setLoading(false);
    }
  };

  /* =========================================================
     RESET TO LANDING
  ========================================================= */

  const resetRepository = () => {
    setAnalysis(null);
    setRepoUrl("");

    setSelectedFile(null);
    setFileContent("");
    setFileError("");
    setFileLoading(false);

    setError("");

    setChatMessages([]);
    setChatQuestion("");
    setChatError("");
    setChatLoading(false);
  };

  /* =========================================================
     COMMAND CENTER
  ========================================================= */

  if (analysis) {
    const repo = analysis.repository;

    return (
      <main className="dashboard">
        {/* =====================================================
            TOP BAR
        ===================================================== */}

        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">
              <img
                src={Logo}
                alt="Repo-Parth Logo"
              />
            </div>

            <span>Repo-Parth</span>
          </div>

          <div className="command-repo">
            <span className="command-repo-label">
              ANALYZED
            </span>

            <span className="command-repo-name">
              {repo.full_name}
            </span>
          </div>

          <div className="topbar-actions">
            <div className="topbar-status">
              <span />
              ONLINE
            </div>

            <button
              className="new-analysis"
              onClick={resetRepository}
            >
              Analyze another repo
            </button>
          </div>
        </header>

        {/* =====================================================
            REPOSITORY COMMAND HEADER
        ===================================================== */}

        <section className="command-header">
          <div className="command-header-main">
            <div className="eyebrow">
              <span>GH</span>
              GitHub Repository
            </div>

            <div className="command-title-row">
              <h1>{repo.name}</h1>

              <a
                href={repo.html_url}
                target="_blank"
                rel="noreferrer"
                className="repo-external-link"
              >
                Open GitHub
                <ExternalLink size={13} />
              </a>
            </div>

            <p>
              {repo.description ||
                "No repository description available."}
            </p>
          </div>

          <div className="command-metrics">
            <div className="command-metric">
              <span>BRANCH</span>

              <strong>
                <GitBranch size={14} />
                {repo.default_branch}
              </strong>
            </div>

            <div className="command-metric">
              <span>FILES</span>

              <strong>
                {analysis.file_count}
              </strong>
            </div>

            <div className="command-metric">
              <span>LANGUAGE</span>

              <strong>
                {repo.language || "Mixed"}
              </strong>
            </div>
          </div>
        </section>

        {/* =====================================================
            COMMAND CENTER
        ===================================================== */}

        <section className="command-center">
          {/* ===================================================
              LEFT — FILE EXPLORER
          =================================================== */}

          <aside className="command-explorer">
            <div className="command-panel-header">
              <div>
                <span className="panel-kicker">
                  CODEBASE
                </span>

                <h2>Explorer</h2>
              </div>

              <span className="file-count">
                {analysis.file_count}
              </span>
            </div>

            <div className="command-tree">
              {Object.entries(fileTree).map(
                ([folder, paths]) => (
                  <div
                    className="command-tree-group"
                    key={folder}
                  >
                    {folder !== "root" && (
                      <div className="command-folder">
                        <FolderOpen size={14} />

                        <span>{folder}</span>

                        <span className="folder-count">
                          {paths.length}
                        </span>
                      </div>
                    )}

                    <div className="command-folder-files">
                      {paths.map((path) => {
                        const file =
                          analysis.files.find(
                            (item) =>
                              item.path === path
                          );

                        if (!file) {
                          return null;
                        }

                        const displayName =
                          folder === "root"
                            ? path
                            : path.slice(
                                folder.length + 1
                              );

                        const isSelected =
                          selectedFile?.path ===
                          file.path;

                        return (
                          <button
                            key={file.path}
                            className={`command-file ${
                              isSelected
                                ? "selected"
                                : ""
                            }`}
                            onClick={() =>
                              selectFile(file)
                            }
                            title={file.path}
                          >
                            <FileCode2 size={14} />

                            <span>
                              {displayName}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )
              )}
            </div>
          </aside>

          {/* ===================================================
              CENTER — SOURCE CODE
          =================================================== */}

          <main className="command-source">
            {!selectedFile ? (
              <div className="source-empty">
                <div className="source-empty-icon">
                  <FileCode2 size={24} />
                </div>

                <span className="panel-kicker">
                  SOURCE INTELLIGENCE
                </span>

                <h2>Select a file.</h2>

                <p>
                  Choose a file from the explorer
                  to inspect its source code.
                </p>

                <div className="source-empty-meta">
                  <span>
                    {analysis.file_count} files indexed
                  </span>

                  <span>
                    {analysis.technologies.length}{" "}
                    technologies detected
                  </span>
                </div>
              </div>
            ) : (
              <div className="source-workspace">
                {/* SOURCE HEADER */}

                <div className="source-header">
                  <div className="source-file-info">
                    <div className="source-file-icon">
                      <FileCode2 size={17} />
                    </div>

                    <div>
                      <span className="source-label">
                        SOURCE FILE
                      </span>

                      <h2 title={selectedFile.path}>
                        {selectedFile.path}
                      </h2>
                    </div>
                  </div>

                  <button
                    className="source-close"
                    onClick={clearSelectedFile}
                  >
                    <ArrowLeft size={14} />
                    Overview
                  </button>
                </div>

                {/* FILE META */}

                <div className="source-meta">
                  <span>
                    TYPE{" "}
                    <strong>
                      {selectedFile.path
                        .split(".")
                        .pop()
                        ?.toUpperCase() ||
                        "FILE"}
                    </strong>
                  </span>

                  <span>
                    SIZE{" "}
                    <strong>
                      {selectedFile.size ?? 0} bytes
                    </strong>
                  </span>

                  <span>
                    BRANCH{" "}
                    <strong>
                      {repo.default_branch}
                    </strong>
                  </span>
                </div>

                {/* SOURCE */}

                <div className="source-code-wrapper">
                  {fileLoading && (
                    <div className="source-loading">
                      <Loader2
                        size={18}
                        className="spin"
                      />

                      <span>
                        Reading source code...
                      </span>
                    </div>
                  )}

                  {fileError && (
                    <div className="source-error">
                      {fileError}
                    </div>
                  )}

                  {!fileLoading &&
                    !fileError &&
                    fileContent && (
                      <pre className="source-code">
                        <code>
                          {fileContent}
                        </code>
                      </pre>
                    )}
                </div>
              </div>
            )}
          </main>

          {/* ===================================================
              RIGHT — PARTH AI
          =================================================== */}

          <aside className="command-ai">
            <div className="ai-header">
              <div className="ai-heading">
                <div className="ai-symbol">
                  <Sparkles size={15} />
                </div>

                <div>
                  <h2>Parth AI</h2>

                  <p>
                    Repository intelligence
                  </p>
                </div>
              </div>

              <div className="ai-status">
                <span />
                Online
              </div>
            </div>

            {/* CHAT */}

            <div className="chat-messages">
              {chatMessages.length === 0 && (
                <div className="chat-empty">
                  <div className="chat-empty-icon">
                    <Sparkles size={24} />
                  </div>

                  <span className="panel-kicker">
                    PARTH INTELLIGENCE
                  </span>

                  <h3>
                    Understand your codebase.
                  </h3>

                  <p>
                    Ask questions about architecture,
                    files, functions, frameworks,
                    or how different parts of the
                    repository work.
                  </p>

                  <div className="suggested-questions">
                    <button
                      onClick={() =>
                        setChatQuestion(
                          "How does authentication work?"
                        )
                      }
                    >
                      How does authentication work?
                    </button>

                    <button
                      onClick={() =>
                        setChatQuestion(
                          "Trace the API request flow."
                        )
                      }
                    >
                      Trace the API request flow.
                    </button>

                    <button
                      onClick={() =>
                        setChatQuestion(
                          "Which files are most important?"
                        )
                      }
                    >
                      Which files are most important?
                    </button>

                    <button
                      onClick={() =>
                        setChatQuestion(
                          "How are the main modules connected?"
                        )
                      }
                    >
                      How are the main modules connected?
                    </button>
                  </div>
                </div>
              )}

              {chatMessages.map(
                (message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`chat-message ${message.role}`}
                  >
                    <div className="chat-message-label">
                      {message.role === "user"
                        ? "YOU"
                        : "PARTH"}
                    </div>

                    <div className="chat-message-content">
                      <div className="chat-answer">
                        {message.content}
                      </div>

                      {/* =================================================
                          AI SOURCE EVIDENCE
                      ================================================= */}

                      {message.role ===
                        "assistant" &&
                        message.sources &&
                        message.sources.length >
                          0 && (
                          <div className="chat-sources">
                            <div className="chat-sources-title">
                              Evidence
                            </div>

                            <div className="chat-sources-list">
                              {message.sources.map(
                                (source) => {
                                  const repositoryFile =
                                    analysis.files.find(
                                      (file) =>
                                        file.path ===
                                        source
                                    );

                                  return (
                                    <button
                                      key={source}
                                      className={`chat-source ${
                                        repositoryFile
                                          ? "clickable"
                                          : "unavailable"
                                      }`}
                                      onClick={() => {
                                        if (
                                          repositoryFile
                                        ) {
                                          selectFile(
                                            repositoryFile
                                          );
                                        }
                                      }}
                                      disabled={
                                        !repositoryFile
                                      }
                                      title={
                                        repositoryFile
                                          ? `Open ${source}`
                                          : "Source file is not available in the indexed repository"
                                      }
                                    >
                                      <FileCode2
                                        size={13}
                                      />

                                      <span>
                                        {source}
                                      </span>

                                      {repositoryFile && (
                                        <ArrowRight
                                          size={12}
                                        />
                                      )}
                                    </button>
                                  );
                                }
                              )}
                            </div>
                          </div>
                        )}

                      {/* =================================================
                          FILE RELATIONSHIPS
                      ================================================= */}

                      {message.role ===
                        "assistant" &&
                        message.relationships &&
                        message.relationships.length >
                          0 && (
                          <div className="chat-relationships">
                            <div className="chat-relationships-title">
                              File Connections
                            </div>

                            <div className="chat-relationships-list">
                              {message.relationships
                                .slice(0, 8)
                                .map(
                                  (
                                    relationship,
                                    relationshipIndex
                                  ) => {
                                    const sourceFile =
                                      analysis.files.find(
                                        (file) =>
                                          file.path ===
                                          relationship.source
                                      );

                                    const targetFile =
                                      analysis.files.find(
                                        (file) =>
                                          file.path ===
                                          relationship.target
                                      );

                                    const sourceName =
                                      relationship.source
                                        .split("/")
                                        .pop() ||
                                      relationship.source;

                                    const targetName =
                                      relationship.target
                                        .split("/")
                                        .pop() ||
                                      relationship.target;

                                    return (
                                      <div
                                        className="chat-relationship"
                                        key={`${relationship.source}-${relationship.target}-${relationshipIndex}`}
                                      >
                                        <button
                                          className="chat-relationship-file"
                                          onClick={() => {
                                            if (
                                              sourceFile
                                            ) {
                                              selectFile(
                                                sourceFile
                                              );
                                            }
                                          }}
                                          disabled={
                                            !sourceFile
                                          }
                                          title={
                                            relationship.source
                                          }
                                        >
                                          <span className="chat-relationship-file-icon">
                                            ↗
                                          </span>

                                          <span>
                                            {sourceName}
                                          </span>
                                        </button>

                                        <div className="chat-relationship-type">
                                          <span className="chat-relationship-line" />

                                          <span>
                                            {
                                              relationship.type
                                            }
                                          </span>

                                          <span className="chat-relationship-arrow">
                                            →
                                          </span>
                                        </div>

                                        <button
                                          className="chat-relationship-file"
                                          onClick={() => {
                                            if (
                                              targetFile
                                            ) {
                                              selectFile(
                                                targetFile
                                              );
                                            }
                                          }}
                                          disabled={
                                            !targetFile
                                          }
                                          title={
                                            relationship.target
                                          }
                                        >
                                          <span className="chat-relationship-file-icon">
                                            ↗
                                          </span>

                                          <span>
                                            {targetName}
                                          </span>
                                        </button>
                                      </div>
                                    );
                                  }
                                )}
                            </div>
                          </div>
                        )}
                    </div>
                  </div>
                )
              )}

              {/* =================================================
                  AI THINKING STATE
              ================================================= */}

              {chatLoading && (
                <div className="chat-message assistant">
                  <div className="chat-message-label">
                    PARTH
                  </div>

                  <div className="chat-message-content ai-thinking">
                    <Loader2
                      size={14}
                      className="spin"
                    />

                    <span>
                      Tracing the repository...
                    </span>
                  </div>
                </div>
              )}
            </div>

            {chatError && (
              <div className="chat-error">
                {chatError}
              </div>
            )}

            {/* =================================================
                CHAT INPUT
            ================================================= */}

            <div className="chat-input-area">
              <textarea
                value={chatQuestion}
                onChange={(event) =>
                  setChatQuestion(
                    event.target.value
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();
                    askRepoParth();
                  }
                }}
                placeholder="Ask Parth about this repository..."
                rows={2}
                disabled={chatLoading}
              />

              <button
                onClick={askRepoParth}
                disabled={
                  chatLoading ||
                  !chatQuestion.trim()
                }
                className="ask-ai-button"
                aria-label="Ask Parth"
              >
                {chatLoading ? (
                  <Loader2
                    size={16}
                    className="spin"
                  />
                ) : (
                  <Send size={16} />
                )}
              </button>
            </div>
          </aside>
        </section>

        {/* =====================================================
            INTELLIGENCE STRIP
        ===================================================== */}

        <section className="intelligence-strip">
          <div className="intelligence-item">
            <span>TECHNOLOGIES</span>

            <div className="intelligence-tags">
              {analysis.technologies
                .slice(0, 8)
                .map((technology) => (
                  <span key={technology}>
                    {technology}
                  </span>
                ))}
            </div>
          </div>

          <div className="intelligence-divider" />

          <div className="intelligence-item">
            <span>IMPORTANT FILES</span>

            <strong>
              {analysis.important_files.length}
            </strong>
          </div>

          <div className="intelligence-divider" />

          <div className="intelligence-item">
            <span>REPOSITORY STATUS</span>

            <strong className="status-live">
              <span />
              INDEXED
            </strong>
          </div>
        </section>
      </main>
    );
  }

  /* =========================================================
     LANDING PAGE
  ========================================================= */

  return (
    <main className="landing">
      <div className="landing-grid" />

      <div className="landing-orbit landing-orbit-one" />

      <div className="landing-orbit landing-orbit-two" />

      <div className="glow glow-one" />

      <div className="glow glow-two" />

      {/* =====================================================
          NAVBAR
      ===================================================== */}

      <nav className="navbar">
        <div className="brand">
          <div className="brand-mark">
            <img
              src={Logo}
              alt="Repo-Parth"
            />
          </div>

          <span>Repo-Parth</span>
        </div>

        <div className="nav-label">
          Repository Intelligence
        </div>
      </nav>

      {/* =====================================================
          HERO
      ===================================================== */}

      <section className="hero">
        <div className="hero-badge">
          <span className="hero-badge-dot" />

          <Sparkles size={13} />

          AI-powered repository intelligence
        </div>

        <div className="hero-kicker">
          <span>01</span>

          CODEBASE INTELLIGENCE SYSTEM
        </div>

        <h1>
          <span className="hero-line">
            Enter the repository.
          </span>

          <span className="hero-line hero-line-gold">
            Understand the code.
          </span>
        </h1>

        <p className="hero-description">
          Repo-Parth maps your GitHub repository,
          uncovers its architecture, identifies
          the important files, and lets you
          interrogate the codebase with AI.
        </p>

        {/* =================================================
            REPOSITORY INPUT
        ================================================= */}

        <div className="analyzer">
          <div className="input-wrapper">
            <div className="github-symbol">
              GH
            </div>

            <div className="input-content">
              <span className="input-label">
                REPOSITORY URL
              </span>

              <input
                type="text"
                placeholder="https://github.com/username/repository"
                value={repoUrl}
                onChange={(event) =>
                  setRepoUrl(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    analyzeRepository();
                  }
                }}
              />
            </div>
          </div>

          <button
            className="analyze-button"
            onClick={analyzeRepository}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2
                  className="spin"
                  size={17}
                />

                Analyzing
              </>
            ) : (
              <>
                Analyze Repository
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {/* =================================================
            CAPABILITIES
        ================================================= */}

        <div className="feature-row">
          <div>
            <span className="feature-index">
              01
            </span>

            <GitBranch size={15} />

            <span>
              Repository mapping
            </span>
          </div>

          <div>
            <span className="feature-index">
              02
            </span>

            <FileCode2 size={15} />

            <span>
              Source intelligence
            </span>
          </div>

          <div>
            <span className="feature-index">
              03
            </span>

            <Sparkles size={15} />

            <span>
              Grounded AI
            </span>
          </div>
        </div>
      </section>

      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer>
        <span className="footer-brand">
          REPO-PARTH
        </span>

        <span>
          Understand code. Faster.
        </span>

        <span>
          <span className="footer-dot" />
          SYSTEM ONLINE
        </span>
      </footer>
    </main>
  );
}

export default App;