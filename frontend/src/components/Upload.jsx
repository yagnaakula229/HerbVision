import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Upload.css';

function Upload({ isAuthenticated }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Redirect if not authenticated
  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      setError('');

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.error);
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-content">
        <h2>Upload Medicinal Plant Image</h2>
        <p>Upload an image of a medicinal plant to identify it and learn about its uses.</p>

        <form onSubmit={handleSubmit} className="upload-form">
          <div className="file-input-group">
            <input
              type="file"
              id="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="file-input"
            />
            <label htmlFor="file" className="file-label">
              Choose Image
            </label>
            {selectedFile && (
              <span className="file-name">{selectedFile.name}</span>
            )}
          </div>

          {preview && (
            <div className="image-preview">
              <img src={preview} alt="Preview" />
            </div>
          )}

          <button
            type="submit"
            disabled={!selectedFile || loading}
            className="upload-button"
          >
            {loading ? 'Analyzing...' : 'Analyze Plant'}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="result-container">
            <h3>Analysis Result</h3>
            {result.image && (
              <div className="result-image">
                <img
                  src={`/upload/${result.image}`}
                  alt="Analyzed plant"
                />
              </div>
            )}
            
            {/* Display top 3 predictions with confidence scores */}
            {result.predictions && result.predictions.length > 0 && (
              <div className="predictions-section">
                <h5>Top 3 Predictions:</h5>
                <div className="predictions-list">
                  {result.predictions.map((pred, index) => (
                    <div key={index} className="prediction-item">
                      <span className="rank">#{index + 1}</span>
                      <span className="plant-name">{pred.plant}</span>
                      <span className="confidence">
                        {(pred.confidence * 100).toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Display main prediction details */}
            {result.main_prediction && (
              <div className="result-details">
                <h4>Primary Result: {result.main_prediction.plant}</h4>
                {result.main_prediction.description && (
                  <div className="result-section">
                    <h5>Description:</h5>
                    <p>{result.main_prediction.description}</p>
                  </div>
                )}
                {result.main_prediction.uses && (
                  <div className="result-section">
                    <h5>Medicinal Uses:</h5>
                    <p>{result.main_prediction.uses}</p>
                  </div>
                )}
              </div>
            )}

            {/* Fallback for old format (in case non-medicinal plant) */}
            {!result.predictions && result.prediction && (
              <div className="result-details">
                <h4>Result: {result.prediction}</h4>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;