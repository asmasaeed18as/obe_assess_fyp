// src/pages/DashboardHome.js
import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthContext from "../contexts/AuthContext";
import api from "../api/axios"; // Your configured axios instance
import "../styles/Dashboard.css";

const DashboardHome = () => {
  const { user } = useContext(AuthContext); // This has basic user info from login
  const navigate = useNavigate();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Call the new API endpoint
        const response = await api.get("/users/dashboard/");
        setDashboardData(response.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Could not load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <div className="p-8">Loading dashboard...</div>;
  if (error) return <div className="p-8 text-red-500">{error}</div>;

  // Use fetched data, fallback to defaults if necessary
  const profileName = dashboardData?.first_name 
    ? `${dashboardData.first_name} ${dashboardData.last_name}`
    : dashboardData?.username || "User";
    
  // Capitalize Role
  const roleDisplay = dashboardData?.role 
    ? dashboardData.role.charAt(0).toUpperCase() + dashboardData.role.slice(1)
    : "Member";

  const courses = dashboardData?.courses || [];

  return (
    <div className="dashboard-content-wrapper fade-in">
      
      {/* === 1. Profile Section (Dynamic) === */}
      <section className="profile-card">
        {/* You can add logic here later to show a real user image if available */}
        <div className="profile-avatar" /> 
        <div>
          <h3 className="profile-name">{profileName}</h3>
          <p className="profile-role">{roleDisplay}</p>
        </div>
      </section>

      {/* === 2. Courses Section (Dynamic) === */}
      <section>
        <h3 className="section-title">My Courses</h3>
        
        <div className="course-grid">
          {courses.length > 0 ? (
            courses.map((course) => (
              <div
                key={course.id}
                className="course-card"
                onClick={() => navigate(`/dashboard/courses/${course.id}`)}
              >
                <h4 className="course-title">{course.title}</h4>
                <div className="course-meta">
                  <span title="Course Code">🏷 {course.code}</span>
                  <span title="Students enrolled">👥 {course.students_count}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-courses-msg">
              <p>You are not enrolled in any courses yet.</p>
            </div>
          )}

          {/* Add/Enroll Course Button */}
          <div
            className="course-card add-course"
            onClick={() => navigate("/dashboard/enroll-course")}
            title="Enroll in a new course"
          >
            +
          </div>
        </div>
      </section>
    </div>
  );
};

export default DashboardHome;