import React, { useState, useEffect } from "react";
import api from "../api/axios";
import "../styles/AdminManager.css";

const AdminManager = () => {
  const [hierarchy, setHierarchy] = useState([]); 
  const [resources, setResources] = useState({ courses: [], instructors: [] }); 

  const [selectedDept, setSelectedDept] = useState("");
  const [selectedProgram, setSelectedProgram] = useState("");
  const [selectedBatch, setSelectedBatch] = useState(null);

  // Modals State
  const [showSectionModal, setShowSectionModal] = useState(false);
  const [showCourseModal, setShowCourseModal] = useState(false); // ✅ New Modal State
  const [modalTargetSemester, setModalTargetSemester] = useState(null);
  const [loading, setLoading] = useState(false);

  // Forms Data
  const [sectionFormData, setSectionFormData] = useState({ course: "", instructor: "", section_name: "Section A" });
  const [courseFormData, setCourseFormData] = useState({ code: "", title: "", credit_hours: 3 }); // ✅ New Form State

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

  // ✅ ACTION: Create a brand new subject in the catalog
  const handleCreateCourseCatalog = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/courses/create/", courseFormData);
      alert("✅ New Course added to Catalog!");
      setShowCourseModal(false);
      setCourseFormData({ code: "", title: "", credit_hours: 3 });
      fetchResources(); // Refresh dropdowns so the new course appears!
    } catch (err) {
      alert("Failed to create course.");
    } finally {
      setLoading(false);
    }
  };

  // ACTION: Assign an existing subject to a teacher
  const handleCreateSection = async (e) => {
    e.preventDefault();
    if (!modalTargetSemester) return;
    setLoading(true);
    try {
      await api.post("/sections/create/", {
        semester: modalTargetSemester.id, ...sectionFormData
      });
      alert("✅ Course Registered to Semester!");
      setShowSectionModal(false);
      fetchHierarchy(); 
    } catch (err) { alert("Failed to register."); } finally { setLoading(false); }
  };

  return (
    <div className="admin-manager-container">
      
      {/* === TOP HEADER AREA === */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h2 style={{ margin: 0 }}>Manage Departments, Programs & Courses</h2>
          <button 
             onClick={() => setShowCourseModal(true)} 
             className="btn-save" 
             style={{ backgroundColor: '#8b5cf6' }} // Purple button to stand out
          >
             + Create New Course (Catalog)
          </button>
      </div>

      {/* === TOP FILTERS === */}
      <div className="filters-bar">
        <div className="filter-group">
          <label>Department</label>
          <select value={selectedDept} onChange={(e) => { setSelectedDept(e.target.value); setSelectedProgram(""); setSelectedBatch(null); }}>
            <option value="">-- Select Dept --</option>
            {hierarchy.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Program</label>
          <select value={selectedProgram} onChange={(e) => { setSelectedProgram(e.target.value); setSelectedBatch(null); }} disabled={!selectedDept}>
            <option value="">-- Select Program --</option>
            {currentDept?.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
      </div>

      {/* === BATCH TABS === */}
      {currentProgram && (
        <div className="batch-tabs-row">
          {currentProgram.batches.length > 0 ? (
            currentProgram.batches.map(batch => (
              <button
                key={batch.id}
                className={`batch-pill ${selectedBatch?.id === batch.id ? "active" : ""}`}
                onClick={() => setSelectedBatch(batch)}
              >
                {batch.name}
              </button>
            ))
          ) : ( <p className="hint-text">No batches found.</p> )}
        </div>
      )}

      {/* === SEMESTER & SECTIONS CONTENT === */}
      <div className="admin-content-area">
        {selectedBatch ? (
          selectedBatch.semesters.map(sem => (
            <div key={sem.id} className="semester-group">
              <div className="semester-title-row">
                <h3>{sem.name}</h3>
                {sem.is_active && (
                  <button className="add-course-btn" onClick={() => { setModalTargetSemester(sem); setShowSectionModal(true); }}>
                    + Register Course
                  </button>
                )}
              </div>

              <div className="admin-course-grid">
                {sem.sections && sem.sections.length > 0 ? (
                  sem.sections.map(section => (
                    <div key={section.id} className="admin-course-card">
                      <div className="acc-header">
                        <span className="acc-code">{section.course_code}</span>
                      </div>
                      <h4>{section.course_title}</h4>
                      <p className="acc-meta"><strong>Sec:</strong> {section.section_name} <br/><strong>Teacher:</strong> {section.instructor_name}</p>
                    </div>
                  ))
                ) : ( <div className="no-courses-placeholder">No courses registered yet.</div> )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-selection-state"><p>Please select a Dept, Program, and Batch.</p></div>
        )}
      </div>

      {/* === MODAL 1: CREATE NEW BASE COURSE (Catalog) === */}
      {showCourseModal && (
        <div className="modal-overlay">
          <div className="modal-box">
            <div className="modal-header">
                <h3>Add New Course to Catalog</h3>
                <button onClick={() => setShowCourseModal(false)} className="close-x">×</button>
            </div>
            <form onSubmit={handleCreateCourseCatalog}>
              <div className="form-field">
                <label>Course Code</label>
                <input type="text" value={courseFormData.code} onChange={e => setCourseFormData({...courseFormData, code: e.target.value})} placeholder="e.g. CS-101" required />
              </div>
              <div className="form-field">
                <label>Course Title</label>
                <input type="text" value={courseFormData.title} onChange={e => setCourseFormData({...courseFormData, title: e.target.value})} placeholder="e.g. Intro to Programming" required />
              </div>
              <div className="form-field">
                <label>Credit Hours</label>
                <input type="number" value={courseFormData.credit_hours} onChange={e => setCourseFormData({...courseFormData, credit_hours: e.target.value})} required min="1" max="6" />
              </div>
              <div className="modal-btns">
                <button type="button" onClick={() => setShowCourseModal(false)} className="btn-cancel">Cancel</button>
                <button type="submit" className="btn-save" disabled={loading}>{loading ? "Saving..." : "Create Course"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* === MODAL 2: REGISTER SECTION (Assign to Teacher) === */}
      {showSectionModal && (
        <div className="modal-overlay">
          <div className="modal-box">
            <div className="modal-header">
                <h3>Register Course for {modalTargetSemester?.name}</h3>
                <button onClick={() => setShowSectionModal(false)} className="close-x">×</button>
            </div>
            <form onSubmit={handleCreateSection}>
              <div className="form-field">
                <label>Select Subject from Catalog</label>
                <select value={sectionFormData.course} onChange={e => setSectionFormData({...sectionFormData, course: e.target.value})} required>
                  <option value="">-- Select Subject --</option>
                  {resources.courses.map(c => <option key={c.id} value={c.id}>{c.code} - {c.title}</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Assign Teacher</label>
                <select value={sectionFormData.instructor} onChange={e => setSectionFormData({...sectionFormData, instructor: e.target.value})} required>
                  <option value="">-- Select Teacher --</option>
                  {resources.instructors.map(i => <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>)}
                </select>
              </div>
              <div className="modal-btns">
                <button type="button" onClick={() => setShowSectionModal(false)} className="btn-cancel">Cancel</button>
                <button type="submit" className="btn-save" disabled={loading}>{loading ? "Saving..." : "Register Section"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminManager;