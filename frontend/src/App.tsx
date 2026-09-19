import { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    axios
      .get("http://localhost:8000/api/health")
      .then((response) => {
        setStatus(response.data.status);
      })
      .catch(() => {
        setStatus("Backend unavailable");
      });
  }, []);

  return (
    <main>
      <h1>Repo-Parth 🏹</h1>
      <p>Backend status: {status}</p>
    </main>
  );
}

export default App;