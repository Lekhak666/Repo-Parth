import { useMemo, useState } from "react";
import axios from "axios";
import {
  ArrowRight,
  GitBranch,
  FileCode2,
  Sparkles,
  Loader2,
} from "lucide-react";
import "./App.css";

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

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [selectedFile, setSelectedFile] =
    useState<RepositoryFile | null>(null);

  const [fileContent, setFileContent] = useState("");
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState("");

  // =========================
  // FILE SELECTION + FETCHING
  // =========================

  const selectFile = async (file: RepositoryFile) => {
    setSelectedFile(file);
    setFileContent("");
    setFileError("");
    setFileLoading(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/repositories/file",
        {
          repo_url: repoUrl,
          file_path: file.path,
        }
      );

      setFileContent(response.data.content);
    } catch (error) {
      console.error(error);
      setFileError("Unable to load this file.");
    } finally {
      setFileLoading(false);
    }
  };

  // =========================
  // REPOSITORY ANALYSIS
  // =========================

  const analyzeRepository = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    setLoading(true);
    setError("");
    setAnalysis(null);
    setSelectedFile(null);
    setFileContent("");
    setFileError("");

    try {
      const response = await axios.post<AnalysisResult>(
        "http://localhost:8000/api/repositories/analyze",
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

  // =========================
  // FILE TREE
  // =========================

  const fileTree = useMemo(() => {
    if (!analysis) {
      return {};
    }

    const tree: Record<string, string[]> = {};

    analysis.files.forEach((file) => {
      const parts = file.path.split("/");

      if (parts.length === 1) {
        if (!tree["root"]) {
          tree["root"] = [];
        }

        tree["root"].push(file.path);
        return;
      }

      const folder = parts[0];

      if (!tree[folder]) {
        tree[folder] = [];
      }

      tree[folder].push(file.path);
    });

    return tree;
  }, [analysis]);

  // =========================
  // DASHBOARD
  // =========================

  if (analysis) {
    const repo = analysis.repository;

    return (
      <main className="dashboard">
        {/* =========================
            TOP BAR
        ========================= */}

        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">🏹</div>
            <span>Repo-Parth</span>
          </div>

          <button
            className="new-analysis"
            onClick={() => {
              setAnalysis(null);
              setRepoUrl("");
              setSelectedFile(null);
              setFileContent("");
              setFileError("");
              setError("");
            }}
          >
            Analyze another repo
          </button>
        </header>

        {/* =========================
            REPOSITORY HEADER
        ========================= */}

        <section className="repo-header">
          <div>
            <div className="eyebrow">
              <span>GH</span>
              GitHub Repository
            </div>

            <h1>{repo.name}</h1>

            <p>
              {repo.description ||
                "No repository description available."}
            </p>

            <a
              href={repo.html_url}
              target="_blank"
              rel="noreferrer"
              className="github-link"
            >
              {repo.full_name}
              <ArrowRight size={15} />
            </a>
          </div>

          <div className="repo-stats">
            <div>
              <span>Branch</span>

              <strong>
                <GitBranch size={15} />
                {repo.default_branch}
              </strong>
            </div>

            <div>
              <span>Files</span>
              <strong>{analysis.file_count}</strong>
            </div>
          </div>
        </section>

        {/* =========================
            EXPLORER
        ========================= */}

        <section className="explorer-layout">
          {/* =========================
              FILE EXPLORER
          ========================= */}

          <aside className="file-explorer">
            <div className="explorer-header">
              <div>
                <span className="panel-kicker">CODEBASE</span>
                <h2>Files</h2>
              </div>

              <span className="file-count">
                {analysis.file_count}
              </span>
            </div>

            <div className="tree">
              {Object.entries(fileTree).map(
                ([folder, paths]) => (
                  <div
                    className="tree-folder"
                    key={folder}
                  >
                    {folder !== "root" && (
                      <div className="folder-name">
                        <span>▾</span>
                        📁 {folder}
                      </div>
                    )}

                    <div className="folder-files">
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

                        return (
                          <button
                            className={`tree-file ${
                              selectedFile?.path ===
                              file.path
                                ? "selected"
                                : ""
                            }`}
                            key={file.path}
                            onClick={() =>
                              selectFile(file)
                            }
                          >
                            <FileCode2 size={14} />

                            <span title={file.path}>
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

          {/* =========================
              REPOSITORY CONTENT
          ========================= */}

          <section className="explorer-content">
            {!selectedFile ? (
              <>
                {/* =========================
                    TECHNOLOGIES
                ========================= */}

                <div className="panel">
                  <div className="panel-heading">
                    <div>
                      <span className="panel-kicker">
                        01
                      </span>

                      <h2>Technologies</h2>
                    </div>

                    <Sparkles size={18} />
                  </div>

                  <div className="technology-list">
                    {analysis.technologies.map(
                      (technology) => (
                        <span
                          key={technology}
                          className="technology"
                        >
                          {technology}
                        </span>
                      )
                    )}
                  </div>
                </div>

                {/* =========================
                    IMPORTANT FILES
                ========================= */}

                <div className="panel">
                  <div className="panel-heading">
                    <div>
                      <span className="panel-kicker">
                        02
                      </span>

                      <h2>Important Files</h2>
                    </div>

                    <FileCode2 size={18} />
                  </div>

                  <div className="file-list">
                    {analysis.important_files
                      .slice(0, 8)
                      .map((file) => (
                        <button
                          className="file-item clickable"
                          key={file.path}
                          onClick={() => {
                            const repositoryFile =
                              analysis.files.find(
                                (item) =>
                                  item.path ===
                                  file.path
                              );

                            if (repositoryFile) {
                              selectFile(
                                repositoryFile
                              );
                            }
                          }}
                        >
                          <FileCode2 size={16} />

                          <div>
                            <strong>
                              {file.path}
                            </strong>

                            <span>
                              {file.role}
                            </span>
                          </div>
                        </button>
                      ))}
                  </div>
                </div>

                {/* =========================
                    PROJECT STRUCTURE
                ========================= */}

                <div className="panel structure-panel">
                  <div className="panel-heading">
                    <div>
                      <span className="panel-kicker">
                        03
                      </span>

                      <h2>Project Structure</h2>
                    </div>
                  </div>

                  <div className="structure">
                    {Object.entries(
                      analysis.project_structure
                    ).map(([folder, items]) => (
                      <div
                        className="structure-group"
                        key={folder}
                      >
                        <strong>{folder}/</strong>

                        <div>
                          {items
                            .slice(0, 8)
                            .map((item) => (
                              <span key={item}>
                                {item}
                              </span>
                            ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              /* =========================
                 SELECTED FILE
              ========================= */

              <div className="panel selected-file-panel">
                <button
                  className="back-button"
                  onClick={() => {
                    setSelectedFile(null);
                    setFileContent("");
                    setFileError("");
                  }}
                >
                  ← Back to repository
                </button>

                <div className="selected-file-title">
                  <FileCode2 size={24} />

                  <div>
                    <span>Selected file</span>

                    <h2>{selectedFile.path}</h2>
                  </div>
                </div>

                {/* FILE METADATA */}

                <div className="file-metadata">
                  <div>
                    <span>Type</span>

                    <strong>
                      {selectedFile.path
                        .split(".")
                        .pop()
                        ?.toUpperCase() ||
                        "FILE"}
                    </strong>
                  </div>

                  <div>
                    <span>Size</span>

                    <strong>
                      {selectedFile.size ?? 0} bytes
                    </strong>
                  </div>
                </div>

                {/* SOURCE CODE */}

                <div className="file-explanation">
                  <span className="panel-kicker">
                    REPO-PARTH
                  </span>

                  <h3>Source Code</h3>

                  {fileLoading && (
                    <p className="file-status">
                      Reading source code...
                    </p>
                  )}

                  {fileError && (
                    <p className="file-status error">
                      {fileError}
                    </p>
                  )}

                  {!fileLoading &&
                    !fileError &&
                    fileContent && (
                      <pre className="source-code">
                        <code>{fileContent}</code>
                      </pre>
                    )}
                </div>
              </div>
            )}
          </section>
        </section>
      </main>
    );
  }

  // =========================
  // LANDING PAGE
  // =========================

  return (
    <main className="landing">
      <div className="glow glow-one" />
      <div className="glow glow-two" />

      <nav className="navbar">
        <div className="brand">
          <div className="brand-mark">🏹</div>
          <span>Repo-Parth</span>
        </div>

        <div className="nav-label">
          Repository Intelligence
        </div>
      </nav>

      <section className="hero">
        <div className="hero-badge">
          <Sparkles size={14} />
          AI-powered repository intelligence
        </div>

        <h1>
          Understand any
          <br />
          <span>GitHub repository.</span>
        </h1>

        <p className="hero-description">
          Give Repo-Parth a repository and let it map
          the codebase, identify technologies, explain
          important files, and help you understand how
          everything fits together.
        </p>

        <div className="analyzer">
          <div className="input-wrapper">
            <span>GH</span>

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

          <button
            className="analyze-button"
            onClick={analyzeRepository}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2
                  className="spin"
                  size={18}
                />
                Analyzing...
              </>
            ) : (
              <>
                Analyze Repository
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="feature-row">
          <div>
            <GitBranch size={17} />
            <span>Repository mapping</span>
          </div>

          <div>
            <FileCode2 size={17} />
            <span>Codebase analysis</span>
          </div>

          <div>
            <Sparkles size={17} />
            <span>AI explanations</span>
          </div>
        </div>
      </section>

      <footer>
        <span>Repo-Parth 🏹</span>

        <span>
          Built for developers who want to understand
          code faster.
        </span>
      </footer>
    </main>
  );
}

export default App;