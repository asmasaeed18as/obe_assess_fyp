import React, { useContext } from "react";
import { NavLink, Outlet } from "react-router-dom"; 
import AuthContext from "../contexts/AuthContext";
import "../styles/Dashboard.css";

export default function DashboardLayout() {
  const { user } = useContext(AuthContext);

  if (!user) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      {/* === Fixed Sidebar === */}
      <aside className="sidebar">
        <h2 className="logo">OBE-Assess</h2>

        <nav className="sidebar-nav">
          {/* 'end' prop ensures 'Home' is only active at /dashboard exactly */}
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
      </aside>

      {/* === Dynamic Main Content Area === */}
      <main className="dashboard-main">
        {/* The Outlet renders the child page (Home, Detail, Enroll, etc.) */}
        <Outlet />
      </main>
    </div>
  );
}