import React from "react";
import { useNavigate } from "react-router-dom";

const InstructorView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || [];

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>Professor {user.last_name}</h1>
        <p>Your Active Classes</p>
      </header>

      <div className="course-grid">
        {courses.map((course) => (
          <div 
            key={course.id} 
            className="course-card instructor-card"
            // Clicking card goes to course details
            onClick={() => navigate(`/dashboard/courses/${course.course_id}`)}
          >
            <div className="status-stripe instructor-color"></div>
            <div className="card-body">
                <h4>{course.title}</h4>
                <div className="meta-row">
                    <span className="course-code">{course.code}</span>
                    <span className="badge">{course.section_name}</span>
                </div>
                
                <div className="instructor-actions">
                    <div className="stat">👥 {course.students_count} Students</div>
                    
                    {/* Shortcut Button: Stops propagation so it doesn't open course detail */}
                    <button 
                        className="btn-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/dashboard/courses/${course.course_id}/create-assessment`);
                        }}
                    >
                        + Assessment
                    </button>
                </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InstructorView;