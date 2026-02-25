import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import api from "../api/axios";
import "../styles/Dashboard.css";

const StudentCourseDetail = () => {
  const { id } = useParams(); 
  
  const [course, setCourse] = useState(null);
  const [clos, setClos] = useState([]);
  const [assessments, setAssessments] = useState([]); 
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        const [courseRes, cloRes, assessRes] = await Promise.all([
            api.get(`/courses/${id}/`),
            api.get(`/courses/${id}/clos/`),
            api.get(`/assessment/course/${id}/`)
        ]);
        setCourse(courseRes.data);
        setClos(cloRes.data);
        setAssessments(assessRes.data);
      } catch (err) {
        console.error("Error loading course data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCourseData();
  }, [id]);

  const handleDownloadZip = (assessmentId) => {
    const backendBaseURL = "http://127.0.0.1:8000";
    window.open(`${backendBaseURL}/api/assessment/download-zip/${assessmentId}/docx/`, "_blank");
  };

  if (loading) return <div className="p-8">Loading Course Info...</div>;
  if (!course) return <div className="p-8">Course not found.</div>;

  return (
    <div className="course-detail-container fade-in">
      {/* HEADER - Read Only */}
      <div className="course-header-card">
        <div className="header-left">
          <h1 className="course-page-title">{course.title}</h1>
          <div className="course-tags">
            <span className="tag-badge blue">{course.code}</span>
          </div>
        </div>
      </div>

      {/* CLOs SECTION - Read Only */}
      <section className="assessments-list-section">
        <h3 className="section-subtitle">Course Learning Outcomes (CLOs)</h3>
        <div className="clo-list-container">
          {clos.length > 0 ? (
            clos.map((clo) => (
              <div key={clo.id} className="clo-item-row">
                <div className="clo-content">
                  <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
                      <span className="clo-code">{clo.code}</span>
                      {clo.mapped_plos && clo.mapped_plos.length > 0 && (
                          <div className="plo-tags-list">
                              {clo.mapped_plos.map((plo, idx) => (
                                  <span key={idx} className="plo-badge">{plo}</span>
                              ))}
                          </div>
                      )}
                  </div>
                  <p className="clo-text mt-2">{clo.text}</p>
                </div>
                <div className="clo-meta">
                  <span className={`bloom-badge ${clo.bloom_level ? clo.bloom_level.charAt(0).toLowerCase() : ''}`}>
                    {clo.bloom_level || "N/A"}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-card"><p>No CLOs available yet.</p></div>
          )}
        </div>
      </section>

      {/* ASSESSMENTS SECTION - Download Only */}
      <section className="assessments-list-section">
        <div className="section-header-row">
          <h3 className="section-subtitle">Pending Assessments</h3>
        </div>
        <div className="assessment-grid-list">
          {assessments.length > 0 ? (
            assessments.map((assess) => (
              <div key={assess.id} className="assessment-item-card">
                <div className="assess-info">
                   <span className="tag-badge blue">{assess.assessment_type || "Assessment"}</span>
                   <span className="assess-date">Posted: {new Date(assess.created_at).toLocaleDateString()}</span>
                </div>
                <div className="assess-actions">
                  <button className="action-btn outline-btn" onClick={() => handleDownloadZip(assess.id)}>
                    Download
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-card"><p>No assessments pending.</p></div>
          )}
        </div>
      </section>
    </div>
  );
};

export default StudentCourseDetail;