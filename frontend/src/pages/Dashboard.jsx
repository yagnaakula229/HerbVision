import { useEffect, useState } from "react";
import api from "../api";
import Navbar from "../components/Navbar";
import ImageUpload from "../components/ImageUpload";
import ResultCard from "../components/ResultCard";

function Dashboard() {
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchHistory = async () => {
    try {
      const response = await api.get("/predictions");
      setHistory(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handlePredict = async (file) => {
    setLoading(true);
    setError("");
    setResult(null);
    const formData = new FormData();
    formData.append("image", file);

    try {
      const response = await api.post("/predict", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
      await fetchHistory();
    } catch (err) {
      setError(err.response?.data?.error || "Prediction failed. Please try another image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container">
        <div className="hero">
          <div className="card">
            <h1>Medicinal Plant Detector</h1>
            <p>
              Upload a plant photo and let HerbVision show you the most likely medicinal plant
              along with confidence and usage tips.
            </p>
          </div>
          <ImageUpload onSubmit={handlePredict} loading={loading} error={error} />
        </div>

        {result && <ResultCard result={result} />}

        <section className="card">
          <h2 className="section-heading">Prediction History</h2>
          {history.length === 0 ? (
            <p>No predictions yet. Upload an image to see history.</p>
          ) : (
            <div className="history-grid">
              {history.map((entry) => (
                <div className="history-item" key={entry.id}>
                  <div>
                    <strong>Plant:</strong> {entry.plant}
                  </div>
                  <div>
                    <strong>Confidence:</strong> {Math.round(entry.confidence * 100)}%
                  </div>
                  <div>
                    <strong>Date:</strong> {new Date(entry.createdAt).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}

export default Dashboard;
