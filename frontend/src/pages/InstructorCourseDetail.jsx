import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import "../styles/Dashboard.css";
import "../styles/AssessmentGrading.css";
import "../styles/InstructorCourseDetail.css";

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
        api.get(`/assessment/course/${id}/?t=${timestamp}`),
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

  useEffect(() => {
    fetchCourseData();
  }, [id]);

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
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const saveClo = async (cloId) => {
    try {
      const updatedClos = clos.map((clo) =>
        clo.id === cloId ? { ...clo, ...editFormData } : clo
      );
      setClos(updatedClos);
      setEditingCloId(null);
      await api.patch(`/courses/clo/${cloId}/`, editFormData);
    } catch {
      fetchCourseData();
    }
  };

  const handleDownloadZip = async (assessmentId) => {
    try {
      const res = await api.get(`/assessment/download-zip/${assessmentId}/docx/`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `Assessment_Bundle_${assessmentId}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Zip download failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="main-viewport">
        <div className="glass-card">Loading course data...</div>
      </div>
    );
  }

  return (
    <div className="main-viewport fade-in">
      <header className="page-header course-detail-header">
        <div className="header-text course-detail-title-block">
          <h1>{course.title}</h1>
          <p className="subtitle">{course.code}</p>
        </div>

        <div className="course-detail-overview">
          <div className="course-detail-chip">
            <span className="course-detail-label">Section</span>
            <strong>{course.section_name || "N/A"}</strong>
          </div>
          <div className="course-detail-chip">
            <span className="course-detail-label">Enrollment Code</span>
            <strong>{course.enrollment_code || "N/A"}</strong>
          </div>
          <div className="course-detail-chip">
            <span className="course-detail-label">Students</span>
            <strong>{course.students_count ?? 0}</strong>
          </div>
        </div>
      </header>

      <section className="page-section course-detail-section course-detail-section--panel">
        <div className="section-header course-detail-section-header">
          <div>
            <h3 className="section-subtitle">Learning Outcomes</h3>
          </div>
          <div className="course-detail-actions">
            <button className="action-pill" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              {uploading ? "Extracting..." : "Upload Outline"}
            </button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            style={{ display: "none" }}
          />
        </div>

        {uploadError && <div className="error-msg">{uploadError}</div>}

        <div className="clo-list course-detail-clo-list">
          {clos.length > 0 ? (
            clos.map((clo) => (
              <div key={clo.id} className="glass-card clo-card course-detail-clo-card">
                {editingCloId === clo.id ? (
                  <div className="clo-edit-form">
                    <input
                      className="edit-input-text"
                      value={editFormData.text}
                      onChange={(e) => setEditFormData({ ...editFormData, text: e.target.value })}
                    />
                    <button onClick={() => saveClo(clo.id)} className="action-pill">
                      Save
                    </button>
                  </div>
                ) : (
                  <div className="clo-content course-detail-clo-content">
                    <div className="clo-text-block">
                      <div className="course-detail-tag-row">
                        <span className="course-tag course-tag--clo">{clo.code}</span>
                        <span className="course-tag course-tag--bloom">
                          {clo.bloom_level || "BT N/A"}
                        </span>
                        {clo.mapped_plos?.map((plo, index) => (
                          <span key={index} className="course-tag course-tag--plo">
                            {plo}
                          </span>
                        ))}
                      </div>
                      <p className="course-detail-clo-text">{clo.text}</p>
                    </div>
                    <button
                      onClick={() => {
                        setEditingCloId(clo.id);
                        setEditFormData({ text: clo.text, bloom_level: clo.bloom_level });
                      }}
                      className="edit-icon-btn course-detail-edit-btn"
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state-glass">
              <p>No CLOs extracted. Upload a course outline to begin.</p>
            </div>
          )}
        </div>
      </section>

      <section className="page-section course-detail-section course-detail-section--panel assessment-section">
        <div className="section-header course-detail-section-header">
          <div>
            <h3 className="section-subtitle">Assessments</h3>
          </div>
          <div className="course-detail-actions">
            <button className="action-pill" onClick={() => navigate(`/dashboard/courses/${id}/create-assessment`)}>
              + Create New
            </button>
            <button className="action-pill" onClick={() => navigate(`/dashboard/analytics/${id}`)}>
              View Analytics
            </button>
          </div>
        </div>

        <div className="course-grid course-detail-assessment-grid">
          {assessments.length > 0 ? (
            assessments.map((assess) => (
              <div key={assess.id} className="glass-card course-card course-detail-assessment-card">
                <div className="course-detail-assessment-visual">
                  <div className="course-detail-assessment-visual-glow" />
                  <div className="course-detail-assessment-doc-mark">Doc</div>
                  <div className="course-detail-assessment-body">
                    <div className="course-detail-assessment-copy">
                      <h3>{assess.assessment_type || "Assessment"}</h3>
                      <p className="course-code-text">
                        Created: {new Date(assess.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="course-detail-assessment-footer">
                      <button className="action-pill" onClick={() => handleDownloadZip(assess.id)}>
                        Download
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-glass">
              <p>No assessments created yet.</p>
            </div>
          )}
        </div>
      </section>

      <section className="page-section course-detail-section course-detail-section--panel">
        <div className="section-header course-detail-section-header">
          <div>
            <h3 className="section-subtitle">Analytics</h3>
          </div>
          <div className="course-detail-actions">
            <button className="action-pill" onClick={() => navigate(`/dashboard/analytics/${id}`)}>
              View Course Analytics
            </button>
          </div>
        </div>
        <div className="course-detail-inline-note">
          Review trends and outcomes coverage.
        </div>
      </section>
    </div>
  );
};

export default InstructorCourseDetail;
