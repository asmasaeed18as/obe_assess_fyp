import React from "react";
import { useNavigate } from "react-router-dom";

const StudentView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || [];

  return (
    <div className="main-viewport fade-in">
      {/* ---------- Page Header: Title + Subtitle + Button ---------- */}
      <header className="page-header stacked">
        <div className="header-text">
          <h1>Welcome, {user.first_name || "Student"}</h1>
          <p className="subtitle">
            You are currently enrolled in {courses.length} active {courses.length === 1 ? 'course' : 'courses'}.
          </p>
        </div>
        
        {/* This container adds the space between the text/button and the boxes below */}
        <div className="header-button-container">
          <button 
            className="action-pill" 
            onClick={() => navigate("/dashboard/enroll-course")}
          >
            + Enroll in New Course
          </button>
        </div>
      </header>

      {/* ---------- Course Grid ---------- */}
      <div className="course-grid">
        {courses.length > 0 ? (
          courses.map((course) => (
            <div 
              key={course.id} 
              className="glass-card course-card student-clickable-card"
              onClick={() => navigate(`/dashboard/courses/${course.id}`)}
            >
              <div className="card-icon-header">📚</div>
              <div className="card-content">
                <h3>{course.title}</h3>
                <p className="course-code-text">{course.code} • {course.section_name || "Section A"}</p>
                
                <div className="card-footer-stats">
                  <span className="stat-label">View Course Progress</span>
                  <span className="arrow-icon">➔</span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state-glass">
            <p>No active courses found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentView;