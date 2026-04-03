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
      const response = await fetch('/predict', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.message || 'Upload failed');
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
            {result.status === 'success' && (
              <div className="result-details">
                <h4>Plant Identified: {result.prediction}</h4>
                <div className="result-section">
                  <h5>Confidence: {result.confidence}%</h5>
                </div>
                {result.top_predictions && result.top_predictions.length > 0 && (
                  <div className="result-section">
                    <h5>Top Predictions:</h5>
                    <ul>
                      {result.top_predictions.map((pred, index) => (
                        <li key={index}>
                          {pred.name}: {pred.confidence}%
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="result-section">
                  <h5>Processing Time: {result.processing_time}s</h5>
                </div>
              </div>
            )}
            {result.status === 'rejected' && (
              <div className="result-details">
                <h4>Result: {result.message}</h4>
                <div className="result-section">
                  <h5>Confidence: {result.confidence}%</h5>
                </div>
                <div className="result-section">
                  <h5>Processing Time: {result.processing_time}s</h5>
                </div>
              </div>
            )}
            {result.status === 'error' && (
              <div className="error-message">
                Error: {result.message}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;