import React from "react";
import AdminManager from "./AdminManager"; 
import "../styles/Dashboard.css"; // Ensure global dashboard styles are applied

const AdminView = () => {
  return (
    <div className="main-viewport fade-in">
      {/* ---------- Admin Header ---------- */}
      <header className="page-header stacked">
        <div className="header-text">
          <h1>Admin Dashboard</h1>
          {/* <p className="subtitle">
            Manage institutional hierarchy, programs, and course registrations.
          </p> */}
        </div>
      </header>

      {/* ---------- Hierarchy Management Area ---------- */}
      <div className="admin-content-wrapper">
        <AdminManager />
      </div>
    </div>
  );
};

export default AdminView;