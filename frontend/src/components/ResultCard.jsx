function ResultCard({ predictions }) {
  if (!predictions || predictions.length === 0) {
    return null;
  }

  const mainPrediction = predictions[0];
  const confidencePercent = Math.round(mainPrediction.confidence * 100);

  return (
    <div className="card result-card">
      <h2>Prediction Results</h2>
      <div className="prediction-heading">Top 3 Predictions</div>
      <div className="prediction-list">
        {predictions.map((prediction, index) => {
          const percent = Math.round(prediction.confidence * 100);
          return (
            <div
              key={prediction.plant}
              className={`prediction-item ${index === 0 ? "prediction-top" : ""}`}
            >
              <div className="prediction-rank">
                <span>{index + 1}</span>
              </div>
              <div>
                <div className="prediction-plant">{prediction.plant}</div>
                <div className="prediction-confidence">{percent}% confidence</div>
              </div>
              <div className="prediction-bar">
                <div className="prediction-fill" style={{ width: `${percent}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="top-details">
        <h3>Top Result: {mainPrediction.plant}</h3>
        <div className="result-item">
          <strong>Confidence:</strong> {confidencePercent}%
        </div>
        <div className="tips">
          <strong>Medicinal Uses:</strong>
          <ul>
            {(mainPrediction.uses || mainPrediction.tips || []).map((use, index) => (
              <li key={index}>{use}</li>
            ))}
          </ul>
        </div>
        <div className="tips">
          <strong>Precautions:</strong>
          <ul>
            {(mainPrediction.precautions || ["Consult a healthcare professional before use."]).map(
              (item, index) => (
                <li key={index}>{item}</li>
              )
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default ResultCard;
