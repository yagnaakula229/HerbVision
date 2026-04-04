import { useState } from "react";

function ImageUpload({ onSubmit, loading, error }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [localError, setLocalError] = useState("");

  const handleFileChange = (event) => {
    setLocalError("");
    const file = event.target.files[0];
    if (!file) {
      setSelectedFile(null);
      setPreview(null);
      return;
    }
    if (!file.type.startsWith("image/")) {
      setSelectedFile(null);
      setPreview(null);
      setLocalError("Please select a valid image file.");
      return;
    }
    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setLocalError("Please choose an image before submitting.");
      return;
    }
    setLocalError("");
    onSubmit(selectedFile);
  };

  return (
    <div className="card upload-card">
      <h2>Upload a plant image</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="image/*" onChange={handleFileChange} disabled={loading} />
        {preview && (
          <div className="preview-wrapper">
            <img className="preview-image" src={preview} alt="Upload preview" />
          </div>
        )}
        <button className="button button-primary" type="submit" disabled={loading || !selectedFile}>
          {loading ? (
            <>
              <span className="spinner" />
              Analyzing plant...
            </>
          ) : (
            "Predict Plant"
          )}
        </button>
      </form>
      {(error || localError) && (
        <div className="error-message">{localError || error}</div>
      )}
    </div>
  );
}

export default ImageUpload;
