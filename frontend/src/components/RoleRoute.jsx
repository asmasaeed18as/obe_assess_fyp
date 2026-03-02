// src/components/RoleRoute.jsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Adjust import if needed

const RoleRoute = ({ allowedRoles }) => {
  const { user } = useAuth(); // Assume your AuthProvider gives you the logged-in user

  // If there's no user, or their role isn't in the allowed list, kick them to the dashboard
  if (!user || !allowedRoles.includes(user.role)) {
    // You can redirect them to a generic "Unauthorized" page, or just back home
    alert("You do not have permission to view this page.");
    return <Navigate to="/dashboard" replace />;
  }

  // If they have the right role, let them through!
  return <Outlet />;
};

export default RoleRoute;