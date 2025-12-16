import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import "../styles/Dashboard.css";

const CourseDetail = () => {
  const { id } = useParams(); 
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // States
  const [course, setCourse] = useState(null);
  const [clos, setClos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  
  // Edit State
  const [editingCloId, setEditingCloId] = useState(null);
  const [editFormData, setEditFormData] = useState({ text: "", bloom_level: "" });

  // 1. Fetch Course & CLOs
  const fetchCourseData = async () => {
    try {
      // Fetch Course Info
      const courseRes = await api.get(`/courses/${id}/`);
      setCourse(courseRes.data);

      // Fetch CLOs
      const cloRes = await api.get(`/courses/${id}/clos/`);
      setClos(cloRes.data);
    } catch (err) {
      console.error("Error loading course:", err);
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
      setClos(res.data.clos); // Update UI with new CLOs
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
      // Optimistic Update
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
      fetchCourseData(); // Revert
    }
  };

  if (loading) return <div className="p-8">Loading...</div>;
  if (!course) return <div className="p-8">Course not found.</div>;

  return (
    <div className="course-detail-container fade-in">
      {/* Header */}
      <div className="course-header-card">
        <div className="header-left">
          <h1 className="course-page-title">{course.title}</h1>
          <div className="course-tags">
            <span className="tag-badge blue">{course.code}</span>
            <span className="tag-badge purple">
              Created: {new Date(course.created_at).toLocaleDateString()}
            </span>
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

      {/* CLOs Section */}
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
                      <option value="C1">C1 - Remember</option>
                      <option value="C2">C2 - Understand</option>
                      <option value="C3">C3 - Apply</option>
                      <option value="C4">C4 - Analyze</option>
                      <option value="C5">C5 - Evaluate</option>
                      <option value="C6">C6 - Create</option>
                    </select>
                    <button onClick={() => saveClo(clo.id)} className="save-btn">💾</button>
                    <button onClick={() => setEditingCloId(null)} className="cancel-btn">✕</button>
                  </div>
                ) : (
                  /* VIEW MODE */
                  <>
                    <div className="clo-content">
                      <span className="clo-code">{clo.code}</span>
                      <p className="clo-text">{clo.text}</p>
                    </div>
                    <div className="clo-meta">
                      <span className="bloom-badge">{clo.bloom_level || "N/A"}</span>
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

      {/* Assessments Section */}
      <section className="assessments-list-section">
        <div className="section-header-row">
          <h3 className="section-subtitle">Assessments</h3>
          <button 
            className="create-new-btn"
            onClick={() => navigate("/dashboard/create-assessment")}
          >
            + Create Assessment
          </button>
        </div>
        <div className="empty-state-card">
            <p>No assessments created yet.</p>
        </div>
      </section>
    </div>
  );
};

export default CourseDetail;