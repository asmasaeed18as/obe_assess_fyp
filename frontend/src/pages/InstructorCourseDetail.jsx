import React, { useState, useEffect, useRef } from "react"; // Added useContext
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
// Added AuthContext import
import "../styles/Dashboard.css";

const InstructorCourseDetail = () => {
  const { id } = useParams(); 
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // --- States ---
  const [course, setCourse] = useState(null);
  const [clos, setClos] = useState([]);
  const [assessments, setAssessments] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  
  // --- Edit State ---
  const [editingCloId, setEditingCloId] = useState(null);
  const [editFormData, setEditFormData] = useState({ text: "", bloom_level: "" });

  // 1. Fetch Course, CLOs AND Assessments
  const fetchCourseData = async () => {
    try {
      // Fetch Course Info
      const courseRes = await api.get(`/courses/${id}/`);
      setCourse(courseRes.data);

      // Fetch CLOs (Now includes mapped_plos)
      const cloRes = await api.get(`/courses/${id}/clos/`);
      setClos(cloRes.data);

      // Fetch Assessments
      const assessRes = await api.get(`/assessment/course/${id}/`);
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

  // 2. Upload Outline
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      const res = await api.post(`/courses/${id}/upload-outline/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      alert("Outline uploaded! CLOs extracted successfully.");
      // Update the list with the fresh data from backend
      setClos(res.data.clos); 
    } catch (err) {
      console.error("Upload failed:", err);
      alert("Failed to upload outline.");
    } finally {
      setUploading(false);
    }
  };

  // 3. Edit Logic
  const startEditing = (clo) => {
    setEditingCloId(clo.id);
    setEditFormData({ text: clo.text, bloom_level: clo.bloom_level });
  };

  const saveClo = async (cloId) => {
    try {
      // Optimistic Update (Update UI immediately)
      const updatedClos = clos.map(c => 
        c.id === cloId ? { ...c, ...editFormData } : c
      );
      setClos(updatedClos);
      setEditingCloId(null);

      // Backend Update
      await api.patch(`/courses/clo/${cloId}/`, editFormData);
    } catch (err) {
      console.error("Failed to update CLO", err);
      alert("Failed to save changes.");
      fetchCourseData(); // Revert on failure
    }
  };

  // Helper to download assessment
  const handleDownloadZip = (assessmentId) => {
    const backendBaseURL = "http://127.0.0.1:8000";
    window.open(`${backendBaseURL}/api/assessment/download-zip/${assessmentId}/docx/`, "_blank");
  };

  if (loading) return <div className="p-8">Loading...</div>;
  if (!course) return <div className="p-8">Course not found.</div>;

  return (
    <div className="course-detail-container fade-in">
      {/* --- Header Section --- */}
      <div className="course-header-card">
        <div className="header-left">
          <h1 className="course-page-title">{course.title}</h1>
          <div className="course-tags">
            <span className="tag-badge blue">{course.code}</span>
            {/* <span className="tag-badge purple">
              Created: {new Date(course.created_at).toLocaleDateString()}
            </span> */}
          </div>
        </div>
        <div className="header-right">
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: "none" }} 
            accept=".pdf,.docx" 
            onChange={handleFileUpload}
          />
          <button 
            className="action-btn outline-btn"
            onClick={() => fileInputRef.current.click()}
            disabled={uploading}
          >
            {uploading ? "⚡ Extracting..." : "⬆ Upload Outline"}
          </button>
        </div>
      </div>

      {/* --- CLOs Section --- */}
      <section className="assessments-list-section">
        <h3 className="section-subtitle">Course Learning Outcomes (CLOs)</h3>
        
        <div className="clo-list-container">
          {clos.length > 0 ? (
            clos.map((clo) => (
              <div key={clo.id} className="clo-item-row">
                {editingCloId === clo.id ? (
                  /* EDIT MODE */
                  <div className="clo-edit-form">
                    <span className="clo-code">{clo.code}</span>
                    <input 
                      type="text" 
                      className="edit-input-text"
                      value={editFormData.text}
                      onChange={(e) => setEditFormData({...editFormData, text: e.target.value})}
                    />
                    <select 
                      className="edit-select-bloom"
                      value={editFormData.bloom_level}
                      onChange={(e) => setEditFormData({...editFormData, bloom_level: e.target.value})}
                    >
                      <option value="">Level</option>
                      {['C1','C2','C3','C4','C5','C6','P1','P2','P3','P4','P5','P6','P7','A1','A2','A3','A4','A5'].map(l => (
                          <option key={l} value={l}>{l}</option>
                      ))}
                    </select>
                    <button onClick={() => saveClo(clo.id)} className="save-btn">💾</button>
                    <button onClick={() => setEditingCloId(null)} className="cancel-btn">✕</button>
                  </div>
                ) : (
                  /* VIEW MODE */
                  <>
                    <div className="clo-content">
                      <div style={{display:'flex', flexDirection:'column', gap:'6px'}}>
                        <div style={{display:'flex', alignItems:'center', gap:'10px', flexWrap:'wrap'}}>
                            {/* CLO Code */}
                            <span className="clo-code">{clo.code}</span>
                            
                            {/* ✅ NEW: PLO Mappings Display */}
                            {clo.mapped_plos && clo.mapped_plos.length > 0 && (
                                <div className="plo-tags-list">
                                    {clo.mapped_plos.map((plo, idx) => (
                                        <span key={idx} className="plo-badge">{plo}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                        <p className="clo-text">{clo.text}</p>
                      </div>
                    </div>

                    <div className="clo-meta">
                      <span className={`bloom-badge ${clo.bloom_level ? clo.bloom_level.charAt(0).toLowerCase() : ''}`}>
                        {clo.bloom_level || "N/A"}
                      </span>
                      <button onClick={() => startEditing(clo)} className="edit-icon-btn">✎</button>
                    </div>
                  </>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state-card">
              <p>No CLOs yet. Upload a Course Outline to extract them automatically.</p>
            </div>
          )}
        </div>
      </section>

      {/* --- Assessments Section --- */}
      <section className="assessments-list-section">
        <div className="section-header-row">
          <h3 className="section-subtitle">Assessments</h3>
          <button 
            className="create-new-btn"
            onClick={() => navigate(`/dashboard/courses/${id}/create-assessment`)}
          >
            + Create Assessment
          </button>
        </div>
        
        <div className="assessment-grid-list">
          {assessments.length > 0 ? (
            assessments.map((assess) => (
              <div key={assess.id} className="assessment-item-card">
                <div className="assess-info">
                   <span className="tag-badge blue">{assess.assessment_type || "Assessment"}</span>
                   <span className="assess-date">
                     Created on: {new Date(assess.created_at).toLocaleDateString()}
                   </span>
                </div>
                <div className="assess-actions">
                  <button 
                    className="action-btn outline-btn"
                    onClick={() => handleDownloadZip(assess.id)}
                    title="Download Bundle"
                  >
                    Download
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-card">
              <p>No assessments created yet.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default InstructorCourseDetail;