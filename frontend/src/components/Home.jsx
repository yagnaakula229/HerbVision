import './Home.css';

function Home() {
  return (
    <div className="home">
      <div className="hero">
        <h1>Welcome to HerbVision</h1>
        <p>Identify medicinal plants using advanced AI technology</p>
        <div className="hero-features">
          <div className="feature">
            <h3>🔍 Accurate Identification</h3>
            <p>Upload images of medicinal plants and get instant identification</p>
          </div>
          <div className="feature">
            <h3>📚 Detailed Information</h3>
            <p>Learn about plant descriptions and traditional medicinal uses</p>
          </div>
          <div className="feature">
            <h3>🌿 40+ Plant Species</h3>
            <p>Comprehensive database of medicinal plants</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;