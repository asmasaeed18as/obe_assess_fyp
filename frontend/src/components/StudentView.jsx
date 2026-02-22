import React from "react";
import { useNavigate } from "react-router-dom";

const StudentView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || []; // Ensure it's an array

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>Hello, {user.first_name || "Student"}!</h1>
        <p>You are enrolled in {courses.length} courses.</p>
      </header>

      <div className="course-grid">
        {courses.length > 0 ? (
          courses.map((course) => (
            <div 
              key={course.id} 
              className="course-card student-card"
              onClick={() => navigate(`/dashboard/courses/${course.id}`)}
            >
              <div className="status-stripe student-color"></div>
              <div className="card-body">
                  <h4>{course.title}</h4>
                  <span className="course-code">{course.code}</span>
                  <div className="card-footer">
                      <span>{course.section_name}</span>
                      <span className="arrow">➔</span>
                  </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p>No active courses found.</p>
            <button onClick={() => navigate("/dashboard/enroll-course")}>
                + Enroll in Course
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentView;