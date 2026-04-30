import React from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, GraduationCap } from "lucide-react";
import "../styles/InstructorView.css";

const InstructorView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || [];
  const displayName = user?.first_name || user?.First_name || user?.username || "Instructor";

  return (
    <div className="instructor-content">
      <header className="page-header page-header--tight">
        <div className="dashboard-hero dashboard-hero--instructor dashboard-hero--compact">
          <div className="dashboard-hero-profile">
            <div className="professor-avatar-placeholder" aria-hidden="true">
              <span>{displayName.charAt(0).toUpperCase()}</span>
            </div>
            <div className="dashboard-hero-copy">
              <h1>Professor {displayName}</h1>
            </div>
          </div>

          <div className="hero-metrics hero-metrics--single">
            <div className="hero-metric-card hero-metric-card--single">
              <GraduationCap size={18} />
              <div>
                <span>Active courses</span>
                <strong>{courses.length}</strong>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section className="dashboard-content">
        <div className="section-header">
          <div>
            <h2 className="section-title">Your Active Classes</h2>
          </div>
        </div>

        <div className="course-grid course-grid--compact">
          {courses.length > 0 ? (
            courses.map((course) => (
              <div
                key={course.course_id}
                className="glass-card course-card instructor-course-card instructor-course-card--minimal"
                onClick={() => navigate(`/dashboard/courses/${course.course_id}`)}
              >
                <div className="course-visual course-visual--instructor course-visual--full">
                  <div className="course-visual-overlay" />
                  <div className="course-visual-badge">
                    <GraduationCap size={18} color="var(--primary)" />
                    <span>Course Cover</span>
                  </div>
                  <div className="course-card-body course-card-body--overlay">
                    <h3>{course.title}</h3>
                    <p className="course-code-text">{course.code}</p>
                    <p className="course-section-text">{course.section_name}</p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-glass">
              <div className="empty-icon">
                <BookOpen size={28} />
              </div>
              <p>No assigned courses found. Please contact your administrator.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default InstructorView;
