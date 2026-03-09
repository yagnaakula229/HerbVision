import './About.css';

function About() {
  return (
    <div className="about">
      <div className="about-container">
        <h1>About HerbVision</h1>

        <section className="about-section">
          <h2>Our Mission</h2>
          <p>
            HerbVision is an AI-powered platform designed to help users identify medicinal plants
            and learn about their traditional uses. We combine cutting-edge machine learning technology
            with extensive botanical knowledge to make plant identification accessible to everyone.
          </p>
        </section>

        <section className="about-section">
          <h2>How It Works</h2>
          <div className="how-it-works">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Upload Image</h3>
              <p>Take a photo of a medicinal plant and upload it to our platform.</p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h3>AI Analysis</h3>
              <p>Our advanced AI model analyzes the image to identify the plant species.</p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h3>Get Information</h3>
              <p>Receive detailed information about the plant's description and medicinal uses.</p>
            </div>
          </div>
        </section>

        <section className="about-section">
          <h2>Technology</h2>
          <p>
            HerbVision uses state-of-the-art deep learning models trained on thousands of medicinal
            plant images. Our system employs a two-stage classification process:
          </p>
          <ul>
            <li><strong>Relevance Check:</strong> Determines if the uploaded image contains a medicinal plant</li>
            <li><strong>Species Classification:</strong> Identifies the specific plant species from our database of 40+ medicinal plants</li>
          </ul>
        </section>

        <section className="about-section">
          <h2>Supported Plants</h2>
          <p>
            Our database includes information about various medicinal plants such as:
          </p>
          <div className="plant-examples">
            <span className="plant-tag">Wood Sorrel</span>
            <span className="plant-tag">Brahmi</span>
            <span className="plant-tag">Basale</span>
            <span className="plant-tag">Lemon Grass</span>
            <span className="plant-tag">Insulin Plant</span>
            <span className="plant-tag">Amruta Balli</span>
            <span className="plant-tag">Aloe Vera</span>
            <span className="plant-tag">Tulasi</span>
            <span className="plant-tag">Neem</span>
            <span className="plant-tag">And many more...</span>
          </div>
        </section>

        <section className="about-section">
          <h2>Contact Us</h2>
          <p>
            Have questions or feedback? We'd love to hear from you. This platform was developed
            to promote awareness and knowledge about medicinal plants and their traditional uses.
          </p>
        </section>
      </div>
    </div>
  );
}

export default About;