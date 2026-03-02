import React from "react";
import { useNavigate } from "react-router-dom";
import { GraduationCap, Users } from "lucide-react";

const InstructorView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || [];

  return (
    <div className="instructor-content">
      <header className="page-header">
        <h1>Professor {user?.First_name || user?.username || ""}</h1>
        <p className="subtitle">Welcome back to your AI Powered OBE Assessemnt System</p>
      </header>

      <section className="dashboard-content">
        <div className="section-header">
           <h2 className="section-title">Your Active Classes</h2>
           {/* Removed New Course Button as per request */}
        </div>
        
        <div className="course-grid">
          {courses.length > 0 ? (
            courses.map((course) => (
              <div 
                key={course.course_id} 
                className="glass-card course-card"
                onClick={() => navigate(`/dashboard/courses/${course.course_id}`)}
              >
                <div className="card-icon-header">
                   <GraduationCap size={22} color="var(--primary)" />
                </div>
                <h3>{course.title}</h3>
                <p className="course-code-text">{course.code} • {course.section_name}</p>
                
                <div className="enrollment-tag">
                  <small>Enrollment Code</small>
                  <code>{course.enrollment_code || "N/A"}</code>
                </div>

                <div className="card-footer-stats">
                  <span className="stat-label"><Users size={14}/> {course.students_count} Students</span>
                  <button 
                    className="action-pill"
                    style={{ 
                      padding: '6px 12px',
                      fontSize: '0.75rem',  
                      borderRadius: '8px', 
                      fontWeight: '600', 
                      minWidth: 'fit-content'   
                     }} 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/dashboard/courses/${course.course_id}/create-assessment`);
                    }}
                  >
                    + Assessment
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-glass">
              <div className="empty-icon">📂</div>
              <p>No assigned courses found. Please contact your administrator.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default InstructorView;
