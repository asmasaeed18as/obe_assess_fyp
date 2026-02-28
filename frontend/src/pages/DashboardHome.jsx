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
        const token = localStorage.getItem("access_token");
        const res = await api.get("/users/dashboard-data/"); 
        setDashboardData(res.data);
      } catch (err) {
        console.error("Error loading dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    
    if (user) {
        fetchData();
    }
  }, [user]);

  if (loading) return <div className="main-viewport"><div className="glass-card">Loading Dashboard...</div></div>;

  // 1. Normalize the role (Priority: Database API -> Auth Context -> Default to student)
  const rawRole = dashboardData?.role || user?.role || "student";
  const currentRole = rawRole.toLowerCase().trim(); 

  // 2. Prepare a clean user profile object
  // This merges the Auth Context (names, username) with Dashboard Data (courses, stats)
  const fullUserContext = { ...user, ...dashboardData };

  console.log("Rendering Dashboard for Role:", currentRole);

  // 3. The Switch Logic
  // Check for admin first to prevent superusers from being trapped in student view
  if (currentRole === "admin" || currentRole === "qa" || currentRole === "superuser" || user?.is_superuser) {
      return <AdminView user={fullUserContext} data={dashboardData} />;
  }
  
  if (currentRole === "instructor") {
      return <InstructorView user={fullUserContext} data={dashboardData} />;
  }

  // Final Fallback: Student View
  return <StudentView user={fullUserContext} data={dashboardData} />;
};

export default DashboardHome;
