import React, { useContext } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom"; 
import AuthContext from "../contexts/AuthContext";
// Added LayoutDashboard for the Admin link icon
import { Home, FilePlus, GraduationCap, BarChart2, Settings, LogOut, LayoutDashboard } from "lucide-react"; 
import "../styles/Dashboard.css";
import logo from "../assets/obe-logo.png";

export default function DashboardLayout() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  if (!user) return <div className="loading-screen">Loading...</div>;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="dashboard-container">
      <aside className="glass-sidebar">
        <div className="sidebar-header">
          <div className="logo-box">
             <img src={logo} alt="Logo" style={{width: '32px'}} />
          </div>
          <span className="brand-name">OBE-Assess</span>
        </div>
        
        <nav className="sidebar-menu">
          {/* Default Home Link */}
          <NavLink to="/dashboard" end className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}>
            <Home size={20}/> Home
          </NavLink>
          
          {/* ADMIN ONLY: Explicit Admin Console Link */}
          {(user.role === "admin" || user.is_superuser) && (
            <NavLink to="/dashboard/admin" className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}>
              <LayoutDashboard size={20}/> Admin Console
            </NavLink>
          )}

          {/* INSTRUCTOR ONLY: Assessment & Grading */}
          {user.role === "instructor" && (
            <>
              <NavLink to="/dashboard/create-assessment" className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}>
                <FilePlus size={20}/> Assessments
              </NavLink>
              <NavLink to="/dashboard/grading" className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}>
                <GraduationCap size={20}/> Grading
              </NavLink>
            </>
          )}

          {/* SHARED LINKS */}
          <NavLink to="/dashboard/analytics" className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}>
            <BarChart2 size={20}/> Analytics
          </NavLink>
          
          <NavLink to="/dashboard/settings" className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}>
            <Settings size={20}/> Settings
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-card-mini">
            <div className="avatar-circle">
              {user?.username?.[0].toUpperCase() || "U"}
            </div>
            <div className="user-info">
              <p className="u-name">{user?.last_name || user?.username}</p>
              <p className="u-role">{user.role}</p>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </aside>

      <main className="main-viewport">
        <Outlet />
      </main>
    </div>
  );
}