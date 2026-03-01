import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import "../styles/Dashboard.css";
import "../styles/AssessmentGrading.css";

const InstructorCourseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [course, setCourse] = useState(null);
  const [clos, setClos] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [editingCloId, setEditingCloId] = useState(null);
  const [editFormData, setEditFormData] = useState({ text: "", bloom_level: "" });

  const fetchCourseData = async () => {
    try {
      const timestamp = new Date().getTime();
      const [courseRes, cloRes, assessRes] = await Promise.all([
        api.get(`/courses/${id}/?t=${timestamp}`),
        api.get(`/courses/${id}/clos/?t=${timestamp}`),
        api.get(`/assessment/course/${id}/?t=${timestamp}`)
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

  useEffect(() => { fetchCourseData(); }, [id]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    setUploadError("");
    try {
      const res = await api.post(`/courses/${id}/upload-outline/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setClos(res.data.clos);
    } catch (err) {
      const message = err?.response?.data?.error || err?.message || "Failed to upload outline.";
      setUploadError(message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const saveClo = async (cloId) => {
    try {
      const updatedClos = clos.map(c => c.id === cloId ? { ...c, ...editFormData } : c);
      setClos(updatedClos);
      setEditingCloId(null);
      await api.patch(`/courses/clo/${cloId}/`, editFormData);
    } catch {
      fetchCourseData();
    }
  };

  const handleDownloadZip = (assessmentId) => {
    const backendBaseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
    window.open(`${backendBaseURL}/api/assessment/download-zip/${assessmentId}/docx/`, "_blank");
  };

  if (loading) return <div className="main-viewport"><div className="glass-card">Loading course data...</div></div>;

  return (
    <div className="main-viewport fade-in">

      {/* ---------- Page Header: Title + Button Underneath ---------- */}
      <header className="page-header stacked">
        <div className="header-text">
          <h1>{course.title}</h1>
          <p className="subtitle">{course.code}</p>
          <p className="subtitle">Instructor Dashboard</p>
        </div>
      </header>

      {/* ---------- CLO Section ---------- */}
      <section className="page-section">
        <div className="section-header stacked">
          <h3 className="section-subtitle">Learning Outcomes</h3>
                  <div className="header-action-row">
          <div className="header-button-container">
          <button className="action-pill" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? "Extracting..." : "Upload Outline"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            style={{ display: "none" }}
          />
          </div>
        </div>
        </div>

        {uploadError && <div className="error-msg">{uploadError}</div>}
        <div className="clo-list">
          {clos.length > 0 ? (
            clos.map((clo) => (
              <div key={clo.id} className="glass-card clo-card">
                {editingCloId === clo.id ? (
                  <div className="clo-edit-form">
                    <input className="edit-input-text" value={editFormData.text} onChange={(e) => setEditFormData({ ...editFormData, text: e.target.value })} />
                    <button onClick={() => saveClo(clo.id)} className="action-pill">Save</button>
                  </div>
                ) : (
                  <div className="clo-content">
                    <div className="clo-text-block">
                      <div className="clo-tags">
                        <span className="tag-badge blue">{clo.code}</span>
                        {clo.mapped_plos?.map((plo, i) => <span key={i} className="tag-badge purple">{plo}</span>)}
                        <span className="bloom-badge">{clo.bloom_level || "N/A"}</span>
                      </div>
                      <p>{clo.text}</p>
                    </div>
                    <button onClick={() => { setEditingCloId(clo.id); setEditFormData({ text: clo.text, bloom_level: clo.bloom_level }); }} className="edit-icon-btn">✎</button>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state-glass"><p>No CLOs extracted. Upload a course outline to begin.</p></div>
          )}
        </div>
      </section>

      {/* ---------- Assessments Section: Subtitle + Button Underneath ---------- */}
      <section className="page-section assessment-section">
        <div className="section-header stacked">
          <h3 className="section-subtitle">Assessments</h3>
          <div className="header-button-container">
          <button className="action-pill" onClick={() => navigate(`/dashboard/courses/${id}/create-assessment`)}>
            + Create New
          </button>
          </div>
        </div>

        <div className="course-grid">
          {assessments.length > 0 ? (
            assessments.map((assess) => (
              <div key={assess.id} className="glass-card course-card">
                <div className="card-icon-header">📄</div>
                <h3>{assess.assessment_type || "Assessment"}</h3>
                <p className="course-code-text">Created: {new Date(assess.created_at).toLocaleDateString()}</p>
                <div className="card-footer-stats">
                  <button className="action-pill" onClick={() => handleDownloadZip(assess.id)}>Download</button>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-glass"><p>No assessments created yet.</p></div>
          )}
        </div>
      </section>
    </div>
  );
};

export default InstructorCourseDetail;
