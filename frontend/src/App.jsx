
import { useState, useEffect } from "react";
import axios from "axios";

import {
  ShieldCheck,
  ShieldAlert,
  Atom,
  User,
  Activity,
  Play,
  History
} from "lucide-react";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [fileHistory, setFileHistory] = useState([]);
const [fileHistoryLoading, setFileHistoryLoading] = useState(false);
  const [originalFile, setOriginalFile] = useState(null);
const [encryptedFile, setEncryptedFile] = useState(null);
const [nonce, setNonce] = useState("");
const [fileMessage, setFileMessage] = useState("");
const [fileLoading, setFileLoading] = useState(false);
  const [eve, setEve] = useState(false);
  const [shots, setShots] = useState(1000);

  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [error, setError] = useState("");
  const [historyError, setHistoryError] = useState("");

  // =====================================
  // FETCH EXCHANGE HISTORY
  // =====================================

  async function fetchHistory() {

    setHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await axios.get(
        `${API_URL}/api/history`
      );

      setHistory(response.data.history);

    } catch (err) {
      setHistoryError("Unable to load exchange history.");
    } finally {
      setHistoryLoading(false);
    }
  }
async function fetchFileHistory() {

  setFileHistoryLoading(true);

  try {
    const response = await axios.get(
      `${API_URL}/api/files/history`
    );

    setFileHistory(response.data.file_history);

  } catch (err) {
    console.error("Unable to fetch file history:", err);
  } finally {
    setFileHistoryLoading(false);
  }
}
  // Fetch history when dashboard loads
useEffect(() => {
  fetchHistory();
  fetchFileHistory();
}, []);

  // =====================================
  // RUN BB84 SIMULATION
  // =====================================

  async function runSimulation() {

    setLoading(true);
    setError("");

    try {

      const response = await axios.post(
        `${API_URL}/api/bb84`,
        {
          n: Number(shots),
          eve_present: eve
        }
      );

      setResult(response.data);

      // Refresh history after saving a simulation
      await fetchHistory();

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to connect to Q-Secure backend."
      );
    } finally {
      setLoading(false);
    }
  }
async function encryptUploadedFile() {

  if (!originalFile) {
    setFileMessage("Please select a file first.");
    return;
  }

  setFileLoading(true);
  setFileMessage("");

  try {
    const formData = new FormData();
    formData.append("file", originalFile);

    const response = await axios.post(
      `${API_URL}/api/files/encrypt`,
      formData,
      { responseType: "blob" }
    );

    const receivedNonce = response.headers["x-nonce"];

    setNonce(receivedNonce);

    const blob = new Blob([response.data], {
      type: "application/octet-stream"
    });

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `encrypted_${originalFile.name}`;
    link.click();

    window.URL.revokeObjectURL(url);

    setFileMessage("File encrypted and downloaded successfully.");

  } catch (err) {
    setFileMessage("Encryption failed. Run a secure BB84 exchange first.");
  } finally {
    setFileLoading(false);
  }
}
async function decryptUploadedFile() {

  if (!encryptedFile || !nonce) {
    setFileMessage("Select the encrypted file and provide its nonce.");
    return;
  }

  setFileLoading(true);
  setFileMessage("");

  try {
    const formData = new FormData();

    formData.append("file", encryptedFile);
    formData.append("nonce", nonce);

    const response = await axios.post(
      `${API_URL}/api/files/decrypt`,
      formData,
      { responseType: "blob" }
    );

    const blob = new Blob([response.data], {
      type: "application/octet-stream"
    });

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `decrypted_${encryptedFile.name}`;
    link.click();

    window.URL.revokeObjectURL(url);

    setFileMessage("File decrypted successfully.");

  } catch (err) {
    setFileMessage("Decryption failed. Check the file, nonce and BB84 key.");
  } finally {
    setFileLoading(false);
  }
}
  // =====================================
  // CHART DATA
  // =====================================

  const chartData = result ? [
    {
      name: "Matching Bases",
      value: result.matching_bases
    },
    {
      name: "Sample Errors",
      value: result.sample_errors
    }
  ] : [];

  // =====================================
  // DASHBOARD UI
  // =====================================

  return (

    <div className="app">

      {/* NAVBAR */}

      <nav className="navbar">

        <h2>
          <Atom /> Q-SECURE
        </h2>

        <span>Quantum Cryptography Platform</span>

      </nav>


      <main className="dashboard">

        <h1>Quantum Security Dashboard</h1>

        <p className="subtitle">
          BB84 Quantum Key Distribution System
        </p>


        {/* PARTICIPANTS */}

        <div className="participants">

          <div className="participant">
            <User />
            <h3>Alice</h3>
            <p>Sender</p>
            <span className="online">Active</span>
          </div>

          <div className="participant">
            <User />
            <h3>Bob</h3>
            <p>Receiver</p>
            <span className="online">Active</span>
          </div>

          <div className="participant eve-card">
            <ShieldAlert />
            <h3>Eve</h3>
            <p>Eavesdropper</p>

            <span className={eve ? "danger" : "online"}>
              {eve ? "Attack Enabled" : "Inactive"}
            </span>
          </div>

        </div>


        {/* SIMULATION CONTROLS */}

        <section className="control-panel">

          <h2>Configure Quantum Exchange</h2>

          <label>Number of Qubits</label>

          <select
            value={shots}
            onChange={e => setShots(e.target.value)}
          >
            <option value="100">100</option>
            <option value="500">500</option>
            <option value="1000">1000</option>
            <option value="5000">5000</option>
          </select>


          <div className="toggle">

            <label>
              Enable Eve's Intercept-and-Resend Attack
            </label>

            <input
              type="checkbox"
              checked={eve}
              onChange={e => setEve(e.target.checked)}
            />

          </div>


          <button
            onClick={runSimulation}
            disabled={loading}
          >

            <Play size={18} />

            {loading ? "Simulating..." : "Run BB84 Simulation"}

          </button>

          {error && <p className="error">{error}</p>}

        </section>


        {/* SIMULATION RESULTS */}

        {result && (

          <section className="results">

            <h2>Simulation Results</h2>

            <div className="status">

              {result.security_status === "SECURE" ?
                <ShieldCheck color="#22c55e" size={40} /> :
                <ShieldAlert color="#ef4444" size={40} />
              }

              <h3>{result.security_status}</h3>

            </div>


            <div className="stats">

              <div className="stat">
                <h3>{result.total_qubits}</h3>
                <p>Total Qubits</p>
              </div>

              <div className="stat">
                <h3>{result.matching_bases}</h3>
                <p>Matching Bases</p>
              </div>

              <div className="stat">
                <h3>{result.qber}%</h3>
                <p>QBER</p>
              </div>

              <div className="stat">
                <h3>{result.key_length}</h3>
                <p>Key Length</p>
              </div>

            </div>


            <h3>
              <Activity /> Exchange Analytics
            </h3>

            <ResponsiveContainer width="100%" height={250}>

              <BarChart data={chartData}>

                <XAxis dataKey="name" stroke="#94a3b8" />

                <YAxis stroke="#94a3b8" />

                <Tooltip />

                <Bar dataKey="value" fill="#38bdf8" />

              </BarChart>

            </ResponsiveContainer>


            <p>
              Database Status: {result.db_saved ?
                "Saved Successfully" : "Not Saved"}
            </p>

            <p>
              Exchange ID: {result.exchange_id ?? "Unavailable"}
            </p>

          </section>

        )}


{/* SECURE FILE TRANSFER */}

<section className="file-panel">

  <h2>Secure File Transfer</h2>

  <p className="subtitle">
    Encrypt and decrypt files using your BB84-derived key.
  </p>

  {/* ENCRYPTION */}

  <div className="file-operation">

    <h3>
      <ShieldCheck /> Alice - Encrypt File
    </h3>

    <input
      type="file"
      onChange={e => setOriginalFile(e.target.files[0] || null)}
    />

    <button
      onClick={encryptUploadedFile}
      disabled={fileLoading}
    >
      {fileLoading ? "Processing..." : "Encrypt and Download"}
    </button>

  </div>

  <div className="file-divider"></div>

  {/* DECRYPTION */}

  <div className="file-operation">

    <h3>
      <ShieldCheck /> Bob - Decrypt File
    </h3>

    <input
      type="file"
      onChange={e => setEncryptedFile(e.target.files[0] || null)}
    />

    <label>Encryption Nonce (X-Nonce)</label>

    <input
      type="text"
      placeholder="Paste the X-Nonce value"
      value={nonce}
      onChange={e => setNonce(e.target.value)}
    />

    <button
      onClick={decryptUploadedFile}
      disabled={fileLoading}
    >
      {fileLoading ? "Processing..." : "Decrypt and Download"}
    </button>

  </div>

  {fileMessage && (
    <p className="file-message">{fileMessage}</p>
  )}

</section>

{/* FILE TRANSFER HISTORY */}

<section className="history-panel">

  <div className="history-heading">

    <h2>
      <History /> File Transfer History
    </h2>

    <button
      className="refresh-button"
      onClick={fetchFileHistory}
      disabled={fileHistoryLoading}
    >
      {fileHistoryLoading ? "Loading..." : "Refresh"}
    </button>

  </div>

  {fileHistoryLoading && fileHistory.length === 0 ? (

    <p>Loading file history...</p>

  ) : fileHistory.length === 0 ? (

    <p>No file transfers found.</p>

  ) : (

    <div className="table-container">

      <table>

        <thead>
          <tr>
            <th>File ID</th>
            <th>Filename</th>
            <th>Exchange ID</th>
            <th>Transfer Date</th>
          </tr>
        </thead>

        <tbody>

          {fileHistory.map(item => (

            <tr key={item.file_id}>

              <td>#{item.file_id}</td>

              <td>{item.filename}</td>

              <td>#{item.exchange_id ?? "N/A"}</td>

              <td>
                {new Date(item.created_at).toLocaleString()}
              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>

  )}

</section>

        {/* EXCHANGE HISTORY */}

        <section className="history-panel">

          <div className="history-heading">

            <h2>
              <History /> Exchange History
            </h2>

            <button
              className="refresh-button"
              onClick={fetchHistory}
              disabled={historyLoading}
            >
              {historyLoading ? "Loading..." : "Refresh"}
            </button>

          </div>


          {historyError && (
            <p className="error">{historyError}</p>
          )}


          {historyLoading && history.length === 0 ? (

            <p>Loading exchange history...</p>

          ) : history.length === 0 ? (

            <p>No exchange records found.</p>

          ) : (

            <div className="table-container">

              <table>

                <thead>

                  <tr>
                    <th>Exchange ID</th>
                    <th>Total Qubits</th>
                    <th>Matching Bases</th>
                    <th>QBER</th>
                    <th>Security Status</th>
                    <th>Date</th>
                  </tr>

                </thead>


                <tbody>

                  {history.map(item => (

                    <tr key={item.exchange_id}>

                      <td>#{item.exchange_id}</td>

                      <td>{item.total_qubits}</td>

                      <td>{item.matching_bases}</td>

                      <td>{item.qber}%</td>

                      <td>

                        <span className={
                          item.security_status === "SECURE"
                            ? "secure-badge"
                            : "unsafe-badge"
                        }>
                          {item.security_status}
                        </span>

                      </td>

                      <td>
                        {new Date(item.created_at).toLocaleString()}
                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </section>

      </main>

    </div>

  );
}

export default App;
