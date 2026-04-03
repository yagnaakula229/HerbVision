import { useState } from "react";

function ImageUpload({ onSubmit, loading, error }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) {
      setSelectedFile(null);
      setPreview(null);
      return;
    }
    if (!file.type.startsWith("image/")) {
      setSelectedFile(null);
      setPreview(null);
      return;
    }
    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!selectedFile) {
      return;
    }
    onSubmit(selectedFile);
  };

  return (
    <div className="card upload-card">
      <h2>Upload a plant image</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="image/*" onChange={handleFileChange} />
        {preview && (
          <div className="preview-wrapper">
            <img className="preview-image" src={preview} alt="Upload preview" />
          </div>
        )}
        <button className="button button-primary" type="submit" disabled={loading || !selectedFile}>
          {loading ? "Predicting..." : "Predict Plant"}
        </button>
      </form>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default ImageUpload;
