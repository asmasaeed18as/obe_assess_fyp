import React from "react";
// Ensure you have AdminManager saved in the same folder or adjust path
import AdminManager from "./AdminManager"; 

const AdminView = () => {
  return (
    <div className="view-container">
      <header className="view-header">
        <h1>Admin Console</h1>
        <p>Manage Departments, Programs, and Course Registrations.</p>
      </header>

      {/* The Hierarchy Dropdowns & Logic */}
      <AdminManager />
    </div>
  );
};

export default AdminView;