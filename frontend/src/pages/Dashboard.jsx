import React, { useContext } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom"; 
import AuthContext from "../contexts/AuthContext";
import "../styles/Dashboard.css";

export default function DashboardLayout() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  if (!user) return <div>Loading...</div>;

  const handleLogout = () => {
    const confirmLogout = window.confirm("Are you sure you want to logout?");
    if (confirmLogout) {
      logout();
      navigate("/login");
    }
  };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <h2 className="logo">OBE-Assess</h2>

        <nav className="sidebar-nav">
          <NavLink 
            to="/dashboard" 
            end
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Home
          </NavLink>
          
          <NavLink 
            to="/dashboard/create-assessment" 
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Assessment Creation
          </NavLink>

          <NavLink 
            to="/dashboard/grading" 
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Assessment Grading
          </NavLink>

          <NavLink 
            to="/dashboard/analytics" 
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Analytics
          </NavLink>

          <NavLink 
            to="/dashboard/settings" 
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Settings
          </NavLink>
        </nav>

        {/* Profile & Logout Section */}
        <div className="sidebar-footer">
          <div className="user-profile-small">
            <div className="user-avatar-mini">
              {user.name ? user.name.charAt(0).toUpperCase() : "A"}
            </div>
            <div className="user-details-mini">
              <span className="user-name-mini">{user.name}</span>
              <span className="user-email-mini">{user.email}</span>
            </div>
          </div>
          

          




          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <Outlet />
      </main>
    </div>
  );
}