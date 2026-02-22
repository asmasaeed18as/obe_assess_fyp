import React, { useContext, useEffect, useState } from "react";
import AuthContext from "../contexts/AuthContext";
import api from "../api/axios";

// Import Sub-Views
import AdminView from "../components/AdminView";
import InstructorView from "../components/InstructorView";
import StudentView from "../components/StudentView";

const DashboardHome = () => {
  const { user } = useContext(AuthContext);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // This endpoint returns the full user profile (including role)
        const res = await api.get("/users/dashboard-data/"); 
        setDashboardData(res.data);
      } catch (err) {
        console.error("Error loading dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    
    // Always fetch data so we get the correct role from the database
    if (user) {
        fetchData();
    }
  }, [user]);

  if (loading) return <div className="p-8">Loading...</div>;

  // === 🛡️ THE FIX IS HERE ===
  // We prefer 'dashboardData.role' because it comes from the DB.
  // We fallback to 'user.role' (from token) only if needed.
  const rawRole = dashboardData?.role || user?.role || "";
  const currentRole = rawRole.toLowerCase(); // Handle "Admin" vs "admin"

  console.log("Determined Role:", currentRole); // Check console to verify

  // === THE SWITCH ===
  // Now we check 'currentRole', not just 'user.role'
  if (currentRole === "admin" || user?.is_superuser) {
      return <AdminView user={dashboardData || user} />;
  }
  
  if (currentRole === "instructor") {
      return <InstructorView user={dashboardData || user} data={dashboardData} />;
  }

  // Default to Student
  return <StudentView user={dashboardData || user} data={dashboardData} />;
};

export default DashboardHome;