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

  // --- NEW: User Registration States ---
  const [showUserModal, setShowUserModal] = useState(false);
  const [userFormData, setUserFormData] = useState({
    first_name: "", last_name: "", email: "", password: "", role: "student"
  });

  const [courseFormData, setCourseFormData] = useState({ code: "", title: "", credit_hours: 3 });
  const [sectionFormData, setSectionFormData] = useState({ course: "", instructor: "", section_names: [] });

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

  // --- ACTION: Register New User ---
  const handleCreateUser = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post("/users/register/", userFormData);
      alert(`✅ ${userFormData.role.toUpperCase()} account created successfully!`);
      setShowUserModal(false);
      setUserFormData({ first_name: "", last_name: "", email: "", password: "", role: "student" });
      fetchResources(); 
    } catch (err) {
      console.error("FULL BACKEND ERROR:", err.response?.data);
      
      let errorMsg = "Failed to create user.";
      if (err.response?.data) {
        // If it's a permission error (403 Forbidden)
        if (err.response.data.detail) {
          errorMsg = err.response.data.detail;
        } else {
          // If it's a validation error (e.g., missing field, email taken)
          errorMsg = JSON.stringify(err.response.data, null, 2);
        }
      }
      
      alert(`DJANGO REJECTED IT! Reason:\n\n${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };
  // --- ACTION: Create Global Course ---
  const handleCreateCourseCatalog = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/courses/create/", courseFormData);
      alert("✅ New Course added to Global Catalog!");
      setShowCourseModal(false);
      setCourseFormData({ code: "", title: "", credit_hours: 3 });
      fetchResources(); 
    } catch (err) { alert(err.response?.data?.error || "Failed to create course."); } finally { setLoading(false); }
  };

  const handleSectionToggle = (secName) => {
    setSectionFormData(prev => {
      const currentSections = prev.section_names;
      if (currentSections.includes(secName)) {
        return { ...prev, section_names: currentSections.filter(s => s !== secName) };
      } else {
        return { ...prev, section_names: [...currentSections, secName] };
      }
    });
  };

  // --- ACTION: Register Instructor to Course ---
  const handleCreateSection = async (e) => {
    e.preventDefault();
    if (!modalTargetSemester) return;
    if (sectionFormData.section_names.length === 0) { alert("Please select at least one section."); return; }

    setLoading(true);
    try {
      const requests = sectionFormData.section_names.map(secName => 
        api.post("/sections/create/", {
          semester: modalTargetSemester.id,
          course: sectionFormData.course,
          instructor: sectionFormData.instructor,
          section_name: secName
        })
      );
      await Promise.all(requests);
      alert(`✅ Successfully registered sections: ${sectionFormData.section_names.join(", ")}!`);
      setShowSectionModal(false);
      setSectionFormData({ course: "", instructor: "", section_names: [] });
      fetchHierarchy(); 
    } catch (err) { 
      let errorMsg = "Failed to register sections. They might already exist.";
      if (err.response?.data?.non_field_errors) errorMsg = err.response.data.non_field_errors[0];
      alert(`Backend Error: ${errorMsg}`); 
    } finally { setLoading(false); }
  };

  return (
    <div className="admin-manager-wrapper">
      
      {/* HEADER WITH NEW BUTTON */}
      <div className="admin-header-area">
        {/* <div className="admin-header-text">
          <h1 className="page-title">Admin Console</h1>
          <p className="subtitle">Manage institutional hierarchy, users, and course registrations.</p>
        </div> */}
        <div className="admin-header-actions">
          <button onClick={() => setShowUserModal(true)} className="action-pill btn-purple">
            + Register User
          </button>
          <button onClick={() => setShowCourseModal(true)} className="action-pill btn-purple">
            + Create New Course
          </button>
        </div>
      </div>

      {/* DROPDOWNS */}
      <div className="glass-card mb-8">
        <div className="filters-container-row">
          <div className="filter-input-group">
            <label>Department</label>
            <select className="glass-select input-field" value={selectedDept} onChange={(e) => { setSelectedDept(e.target.value); setSelectedProgram(""); setSelectedBatch(null); }}>
              <option value="">-- Select Dept --</option>
              {hierarchy.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="filter-input-group">
            <label>Program</label>
            <select className="glass-select input-field" value={selectedProgram} onChange={(e) => { setSelectedProgram(e.target.value); setSelectedBatch(null); }} disabled={!selectedDept}>
              <option value="">-- Select Program --</option>
              {currentDept?.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* BATCH TABS */}
      {currentProgram && (
        <div className="batch-selection-area">
          <p className="section-label">Select Batch</p>
          <div className="tabs-flex-row">
            {currentProgram.batches.map(batch => (
              <button key={batch.id} className={`tab-pill ${selectedBatch?.id === batch.id ? "active" : ""}`} onClick={() => setSelectedBatch(batch)}>
                {batch.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* RESULTS / SEMESTER GRID */}
      <div className="admin-results-container">
        {selectedBatch ? (
          selectedBatch.semesters.map(sem => (
            <div key={sem.id} className="semester-block glass-card">
              <div className="semester-header-row">
                <h3 className="semester-title">Semester {sem.name}</h3>
                <div className="semester-divider"></div>
                {sem.is_active && (
                  <button className="action-pill btn-green-outline" onClick={() => { setModalTargetSemester(sem); setShowSectionModal(true); }}>
                    + Register Instructor
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
                        <p><strong>Sec:</strong> {section.section_name}</p>
                        <p><strong>Instructor:</strong> {section.instructor_name}</p>
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

      {/* ================= MODALS ================= */}

      {/* --- MODAL 1: Create User --- */}
      {showUserModal && (
        <div className="custom-modal-overlay">
          <div className="custom-modal-box">
            <div className="modal-header">
                <h3 className="text-purple">Register New User</h3>
                <button onClick={() => setShowUserModal(false)} className="close-x">&times;</button>
            </div>
            <form onSubmit={handleCreateUser}>
              <div className="form-row">
                <div className="form-field half">
                  <label>First Name</label>
                  <input type="text" className="input-field" value={userFormData.first_name} onChange={e => setUserFormData({...userFormData, first_name: e.target.value})} required />
                </div>
                <div className="form-field half">
                  <label>Last Name</label>
                  <input type="text" className="input-field" value={userFormData.last_name} onChange={e => setUserFormData({...userFormData, last_name: e.target.value})} required />
                </div>
              </div>
              <div className="form-field">
                <label>Email Address</label>
                <input type="email" className="input-field" value={userFormData.email} onChange={e => setUserFormData({...userFormData, email: e.target.value})} required />
              </div>
              <div className="form-field">
                <label>Temporary Password</label>
                <input type="text" className="input-field" value={userFormData.password} onChange={e => setUserFormData({...userFormData, password: e.target.value})} placeholder="Give this to the user" required minLength="8" />
              </div>
              <div className="form-field mb-xl">
                <label>Account Role</label>
                <select className="input-field" value={userFormData.role} onChange={e => setUserFormData({...userFormData, role: e.target.value})} required>
                  <option value="student">Student</option>
                  <option value="instructor">Instructor</option>
                  {/* <option value="qa">Quality Assurance</option>
                  <option value="admin">Admin</option> */}
                </select>
              </div>
              <div className="modal-btns">
                <button type="button" onClick={() => setShowUserModal(false)} className="btn-cancel">Cancel</button>
                <button type="submit" className="btn-save btn-purple" disabled={loading}>{loading ? "Saving..." : "Create Account"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL 2: Create Global Course --- */}
      {showCourseModal && (
        <div className="custom-modal-overlay">
          <div className="custom-modal-box">
            <div className="modal-header">
                <h3 className="text-purple">Add New Course to Catalog</h3>
                <button onClick={() => setShowCourseModal(false)} className="close-x">&times;</button>
            </div>
            <form onSubmit={handleCreateCourseCatalog}>
              <div className="form-field">
                <label>Course Code</label>
                <input type="text" className="input-field" value={courseFormData.code} onChange={e => setCourseFormData({...courseFormData, code: e.target.value})} placeholder="e.g. CS-101" required />
              </div>
              <div className="form-field">
                <label>Course Title</label>
                <input type="text" className="input-field" value={courseFormData.title} onChange={e => setCourseFormData({...courseFormData, title: e.target.value})} placeholder="e.g. Intro to Programming" required />
              </div>
              <div className="form-field mb-xl">
                <label>Credit Hours</label>
                <input type="number" className="input-field" value={courseFormData.credit_hours} onChange={e => setCourseFormData({...courseFormData, credit_hours: e.target.value})} required min="1" max="6" />
              </div>
              <div className="modal-btns">
                <button type="button" onClick={() => setShowCourseModal(false)} className="btn-cancel">Cancel</button>
                <button type="submit" className="btn-save btn-purple" disabled={loading}>{loading ? "Saving..." : "Create Course"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL 3: Register Instructor to Course --- */}
      {showSectionModal && (
        <div className="custom-modal-overlay">
          <div className="custom-modal-box">
            <div className="modal-header">
                <h3 className="text-purple">Register Instructor to {modalTargetSemester?.name}</h3>
                <button onClick={() => setShowSectionModal(false)} className="close-x">&times;</button>
            </div>
            <form onSubmit={handleCreateSection}>
              <div className="form-field">
                <label>Select Subject from Catalog</label>
                <select className="input-field" value={sectionFormData.course} onChange={e => setSectionFormData({...sectionFormData, course: e.target.value})} required>
                  <option value="">-- Select Subject --</option>
                  {resources.courses.map(c => <option key={c.id} value={c.id}>{c.code} - {c.title}</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Assign Teacher</label>
                <select className="input-field" value={sectionFormData.instructor} onChange={e => setSectionFormData({...sectionFormData, instructor: e.target.value})} required>
                  <option value="">-- Select Teacher --</option>
                  {resources.instructors.map(i => <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>)}
                </select>
              </div>
              <div className="form-field mb-xl">
                <label>Assign Sections (Select Multiple)</label>
                <div className="checkbox-group-wrapper">
                  {["Section A", "Section B", "Section C", "Section D", "Section E"].map(sec => (
                    <label key={sec} className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={sectionFormData.section_names.includes(sec)}
                        onChange={() => handleSectionToggle(sec)}
                      />
                      {sec.replace("Section ", "")}
                    </label>
                  ))}
                </div>
              </div>
              <div className="modal-btns">
                <button type="button" onClick={() => setShowSectionModal(false)} className="btn-cancel">Cancel</button>
                <button type="submit" className="btn-save btn-green" disabled={loading}>{loading ? "Saving..." : "Register Instructor"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminManager;