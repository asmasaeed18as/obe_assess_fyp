import React, { useContext } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom"; 
import AuthContext from "../contexts/AuthContext";
import "../styles/Dashboard.css";

export default function DashboardLayout() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  if (!user) return <div>Loading...</div>;

  const isInstructor = user.role === "instructor";
  const isAdmin = user.role === "admin" || user.is_superuser;

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <h2 className="logo">OBE-Assess</h2>

        <nav className="sidebar-nav">
          {/* Everyone sees Home */}
          <NavLink 
            to="/dashboard" 
            end
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Home
          </NavLink>
          
          {/* INSTRUCTOR ONLY: Creation & Grading */}
          {isInstructor && (
            <>
              <NavLink 
                to="/dashboard/create-assessment" 
                className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              >
                Create Assessment
              </NavLink>

              <NavLink 
                to="/dashboard/grading" 
                className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              >
                Grading
              </NavLink>
            </>
          )}

          {/* ADMIN ONLY: Analytics (or maybe everyone?) */}
          {(isAdmin || isInstructor) && (
            <NavLink 
                to="/dashboard/analytics" 
                className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
                Analytics
            </NavLink>
          )}

          {/* Everyone sees Settings */}
          <NavLink 
            to="/dashboard/settings" 
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            Settings
          </NavLink>
        </nav>

        {/* User Mini Profile at Bottom */}
        <div className="sidebar-footer">
            <small>{user.email}</small>
            <div className="role-badge">{user.role}</div>
        </div>
      </aside>

      {/* === Main Content === */}
      <main className="dashboard-main">
        <Outlet />
      </main>
    </div>
  );
}