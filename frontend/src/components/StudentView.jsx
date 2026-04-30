import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, BookOpen, CalendarRange, GraduationCap } from "lucide-react";
import "../styles/StudentView.css";

const StudentView = ({ user, data }) => {
  const navigate = useNavigate();
  const courses = data?.courses || [];
  const displayName = user?.first_name || user?.username || "Student";

  return (
    <div className="fade-in">
      <header className="page-header page-header--tight">
        <div className="dashboard-hero dashboard-hero--student">
          <div className="dashboard-hero-copy">
            <h1>Welcome, {displayName}</h1>
            <p className="subtitle">
              Track enrolled courses and access your learning progress from one organized workspace.
            </p>
          </div>

          <div className="student-hero-actions">
            <div className="hero-metric-card">
              <GraduationCap size={18} />
              <div>
                <strong>{courses.length}</strong>
                <span>Enrolled courses</span>
              </div>
            </div>
            <button
              className="action-pill action-pill--wide"
              onClick={() => navigate("/dashboard/enroll-course")}
            >
              <CalendarRange size={16} /> Enroll in New Course
            </button>
          </div>
        </div>
      </header>

      <section>
        <div className="section-header">
          <div>
            <h2 className="section-title">Your Courses</h2>
          </div>
        </div>

        <div className="course-grid course-grid--compact">
          {courses.length > 0 ? (
            courses.map((course) => (
              <div
                key={course.id}
                className="glass-card course-card student-clickable-card student-course-card"
                onClick={() => navigate(`/dashboard/courses/${course.id}`)}
              >
                <div className="course-visual course-visual--student">
                  <div className="course-visual-overlay" />
                  <div className="course-visual-badge">
                    <BookOpen size={18} color="var(--primary)" />
                    <span>Course Cover</span>
                  </div>
                </div>

                <div className="card-top-row">
                  <div className="card-icon-header">
                    <BookOpen size={20} color="var(--primary)" />
                  </div>
                  <span className="card-status-badge card-status-badge--subtle">Enrolled</span>
                </div>

                <div className="card-content">
                  <h3>{course.title}</h3>
                  <p className="course-code-text">
                    {course.code} - {course.section_name || "Section A"}
                  </p>

                  <div className="student-card-footer">
                    <span className="stat-label">View course progress</span>
                    <span className="card-link-indicator">
                      Open <ArrowRight size={16} />
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-glass">
              <div className="empty-icon">
                <BookOpen size={28} />
              </div>
              <p>No active courses found.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default StudentView;
