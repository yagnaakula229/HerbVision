import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar({ isAuthenticated, user, onLogout }) {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          HerbVision
        </Link>
        <ul className="nav-menu">
          <li className="nav-item">
            <Link to="/" className="nav-link">Home</Link>
          </li>
          <li className="nav-item">
            <Link to="/about" className="nav-link">About</Link>
          </li>
          {isAuthenticated ? (
            <>
              <li className="nav-item">
                <Link to="/upload" className="nav-link">Upload</Link>
              </li>
              <li className="nav-item">
                <span className="nav-user">Welcome, {user}</span>
              </li>
              <li className="nav-item">
                <button onClick={onLogout} className="nav-button">Logout</button>
              </li>
            </>
          ) : (
            <>
              <li className="nav-item">
                <Link to="/login" className="nav-link">Login</Link>
              </li>
              <li className="nav-item">
                <Link to="/register" className="nav-link">Register</Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;