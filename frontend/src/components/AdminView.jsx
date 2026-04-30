import React from "react";
import AdminManager from "./AdminManager"; 
import "../styles/Dashboard.css";
import "../styles/AdminView.css";

const AdminView = () => {
  return (
    <div className="fade-in">
      <header className="page-header page-header--tight">
        <div className="dashboard-hero dashboard-hero--admin">
          <h1>Admin Dashboard</h1>
          <p className="subtitle">
            Manage institutional structure, programs, and course registrations through a cleaner control panel.
          </p>
        </div>
      </header>

      <div className="admin-content-wrapper">
        <AdminManager />
      </div>
    </div>
  );
};

export default AdminView;
