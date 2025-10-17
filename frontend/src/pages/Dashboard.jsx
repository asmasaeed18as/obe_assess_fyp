// src/pages/Dashboard.jsx
import React from "react";
import { NavLink } from "react-router-dom";
import Navbar from "../components/Navbar";
import "../styles/Dashboard.css";

export default function Dashboard() {
  return (
    <div className="dashboard">
      {/* Sidebar */}
      <div className="sidebar">
        <h2>EduPortal</h2>
        <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "active" : "")}>
          Dashboard
        </NavLink>
        <NavLink to="/courses" className={({ isActive }) => (isActive ? "active" : "")}>
          Courses
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => (isActive ? "active" : "")}>
          Profile
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>
          Settings
        </NavLink>
        <NavLink to="/logout" className={({ isActive }) => (isActive ? "active" : "")}>
          Logout
        </NavLink>
      </div>

      {/* Main content */}
      <div className="main-content">
        <div className="card">
          <h3>Welcome to your Dashboard</h3>
          <p>
            Here you can track your courses, assignments, and performance.
          </p>
        </div>

        <div className="card">
          <h3>Upcoming Classes</h3>
          <ul>
            <li>Math Class - Monday 10 AM</li>
            <li>Science Workshop - Wednesday 2 PM</li>
            <li>Sports Training - Friday 5 PM</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
