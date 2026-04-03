function ResultCard({ result }) {
  if (!result) {
    return null;
  }

  const confidencePercent = Math.round(result.confidence * 100);

  return (
    <div className="card result-card">
      <h2>Prediction Result</h2>
      <div className="result-item">
        <strong>Plant:</strong> {result.plant}
      </div>
      <div className="result-item">
        <strong>Confidence:</strong> {confidencePercent}%
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${confidencePercent}%` }} />
      </div>
      <div className="tips">
        <strong>Medicinal Tips:</strong>
        <ul>
          {result.tips.map((tip, index) => (
            <li key={index}>{tip}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default ResultCard;
