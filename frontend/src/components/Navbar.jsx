import React, { useContext } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import AuthContext from "../contexts/AuthContext";
// /import logo from "../assets/logo.png"; // place your logo in src/assets/logo.png
import "../styles/Navbar.css";

export default function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      {/* Left: Logo */}
      <div className="navbar-left">
        {/* <img src={logo} alt="Logo" className="navbar-logo" /> */}
        <span className="navbar-title">EduPortal</span>
      </div>

      {/* Center: Links */}
      <div className="navbar-center">
        <NavLink to="/dashboard" className="nav-link">
          Dashboard
        </NavLink>
        <NavLink to="/courses" className="nav-link">
          Courses
        </NavLink>
        <NavLink to="/profile" className="nav-link">
          Profile
        </NavLink>
      </div>

      {/* Right: User + Logout */}
      <div className="navbar-right">
        {user ? (
          <>
            <span className="navbar-username">{user.username}</span>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </>
        ) : (
          <NavLink to="/login" className="nav-link">
            Login
          </NavLink>
        )}
      </div>
    </nav>
  );
}
