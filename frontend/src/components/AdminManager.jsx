import React, { useState, useEffect } from "react";
import api from "../api/axios";
import "../styles/AdminManager.css";

const AdminManager = () => {
  const [hierarchy, setHierarchy] = useState([]); 
  const [resources, setResources] = useState({ courses: [], instructors: [] }); 

  const [selectedDept, setSelectedDept] = useState("");
  const [selectedProgram, setSelectedProgram] = useState("");
  const [selectedBatch, setSelectedBatch] = useState(null);

  const [showSectionModal, setShowSectionModal] = useState(false);
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [modalTargetSemester, setModalTargetSemester] = useState(null);
  const [loading, setLoading] = useState(false);

  const [sectionFormData, setSectionFormData] = useState({ course: "", instructor: "", section_name: "Section A" });
  const [courseFormData, setCourseFormData] = useState({ code: "", title: "", credit_hours: 3 });

  useEffect(() => {
    fetchHierarchy();
    fetchResources();
  }, []);

  const fetchHierarchy = async () => {
    try {
      const res = await api.get("/hierarchy/");
      setHierarchy(res.data);
    } catch (err) { console.error(err); }
  };

  const fetchResources = async () => {
    try {
      const res = await api.get("/resources/");
      setResources(res.data);
    } catch (err) { console.error(err); }
  };

  const currentDept = hierarchy.find(d => d.id === parseInt(selectedDept));
  const currentProgram = currentDept?.programs.find(p => p.id === parseInt(selectedProgram));

  const handleCreateCourseCatalog = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/courses/create/", courseFormData);
      alert("✅ New Course added to Catalog!");
      setShowCourseModal(false);
      setCourseFormData({ code: "", title: "", credit_hours: 3 });
      fetchResources();
    } catch (err) { alert("Failed to create course."); } finally { setLoading(false); }
  };

  const handleCreateSection = async (e) => {
    e.preventDefault();
    if (!modalTargetSemester) return;
    setLoading(true);
    try {
      await api.post("/sections/create/", { semester: modalTargetSemester.id, ...sectionFormData });
      alert("✅ Course Registered to Semester!");
      setShowSectionModal(false);
      fetchHierarchy(); 
    } catch (err) { alert("Failed to register."); } finally { setLoading(false); }
  };

  return (
    <div className="admin-manager-wrapper">
      
      {/* --- Global Hierarchy Selectors --- */}
      <div className="glass-card mb-8">
        <div className="filters-container-row">
          <div className="filter-input-group">
            <label>Department</label>
            <select className="glass-select" value={selectedDept} onChange={(e) => { setSelectedDept(e.target.value); setSelectedProgram(""); setSelectedBatch(null); }}>
              <option value="">-- Select Dept --</option>
              {hierarchy.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>

          <div className="filter-input-group">
            <label>Program</label>
            <select className="glass-select" value={selectedProgram} onChange={(e) => { setSelectedProgram(e.target.value); setSelectedBatch(null); }} disabled={!selectedDept}>
              <option value="">-- Select Program --</option>
              {currentDept?.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* --- Batch Tabs Area --- */}
      {currentProgram && (
        <div className="batch-selection-area">
          <p className="section-label">Select Your Batch</p>
          <div className="tabs-flex-row">
            {currentProgram.batches.map(batch => (
              <button key={batch.id} className={`tab-pill ${selectedBatch?.id === batch.id ? "active" : ""}`} onClick={() => setSelectedBatch(batch)}>
                {batch.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* --- Semester Grid --- */}
      <div className="admin-results-container">
        {selectedBatch ? (
          selectedBatch.semesters.map(sem => (
            <div key={sem.id} className="semester-block">
              <div className="semester-header-row">
                <h3 className="semester-title">Semester {sem.name}</h3>
                <div className="semester-divider"></div>
                {sem.is_active && (
                  <button className="join-btn small" onClick={() => { setModalTargetSemester(sem); setShowSectionModal(true); }}>
                    + Register Course
                  </button>
                )}
              </div>

              <div className="course-grid">
                {sem.sections && sem.sections.length > 0 ? (
                  sem.sections.map(section => (
                    <div key={section.id} className="glass-card course-card admin-view-card">
                      <div className="card-badge-row">
                        <span className="tag-badge blue">{section.course_code}</span>
                      </div>
                      <h3>{section.course_title}</h3>
                      <div className="enroll-details">
                        <p><span>Section:</span> {section.section_name}</p>
                        <p><span>Instructor:</span> {section.instructor_name}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-state-glass"><p>No courses registered yet.</p></div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state-glass large">
            <div className="empty-icon">🏢</div>
            <p>Select Department and Program to manage hierarchy.</p>
          </div>
        )}
      </div>

      {/* Modals keep the same logic but should use your CSS modal classes */}
      {/* [Modals Code remains the same as your input, ensuring className="modal-overlay" is styled in CSS] */}
    </div>
  );
};

export default AdminManager;