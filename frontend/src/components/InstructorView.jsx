import React from "react";
import { useNavigate } from "react-router-dom";

const InstructorView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || [];

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>Professor {user.last_name || user.first_name || ""}</h1>
        <p>Your Active Classes</p>
      </header>

      <div className="course-grid">
        {courses.map((course) => (
          <div 
            key={course.id} 
            className="course-card instructor-card"
            onClick={() => navigate(`/dashboard/courses/${course.course_id}`)}
          >
            <div className="status-stripe instructor-color"></div>
            <div className="card-body">
                <h4>{course.title}</h4>
                <div className="meta-row">
                    <span className="course-code">{course.code}</span>
                    <span className="badge">{course.section_name}</span>
                </div>
                
                {/* ✅ NEW: Enrollment Code Display */}
                <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px dashed #cbd5e1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase' }}>Enroll Code:</span>
                    <span style={{ fontFamily: 'monospace', fontSize: '1.1rem', fontWeight: 'bold', color: '#2563eb', letterSpacing: '2px' }}>
                        {course.enrollment_code || "N/A"}
                    </span>
                </div>
                
                <div className="instructor-actions" style={{ marginTop: '15px' }}>
                    <div className="stat">👥 {course.students_count} Students</div>
                    
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