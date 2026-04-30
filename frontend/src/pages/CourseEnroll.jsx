import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import "../styles/Dashboard.css"; 

const CourseEnroll = () => {
  const navigate = useNavigate();

  // --- States ---
  const [hierarchy, setHierarchy] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Selection States
  const [selectedDept, setSelectedDept] = useState("");
  const [selectedProgram, setSelectedProgram] = useState("");
  const [selectedBatch, setSelectedBatch] = useState(null);

  // Enrollment Logic States
  const [enrollmentCodes, setEnrollmentCodes] = useState({});
  const [enrollingId, setEnrollingId] = useState(null);

  // 1. Fetch Hierarchy Data
  useEffect(() => {
    const fetchHierarchy = async () => {
      try {
        const res = await api.get("/hierarchy/");
        setHierarchy(res.data);
      } catch (err) {
        console.error("Failed to load hierarchy:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHierarchy();
  }, []);

  // Helpers to get selected objects
  const currentDept = hierarchy.find(d => d.id === parseInt(selectedDept));
  const currentProgram = currentDept?.programs.find(p => p.id === parseInt(selectedProgram));

  // --- Handle Join Request ---
  const handleJoinClass = async (sectionId) => {
    const code = enrollmentCodes[sectionId];
    
    if (!code || code.trim() === "") {
      alert("Please enter the Enrollment Code provided by your instructor.");
      return;
    }

    setEnrollingId(sectionId);
    
    try {
      const res = await api.post("/join/", { enrollment_code: code });
      alert(`✅ Success: ${res.data.message}`);
      navigate("/dashboard"); 
    } catch (err) {
      const errorMessage = err.response?.data?.error || "Failed to join class. Please check the code.";
      alert(`❌ ${errorMessage}`);
    } finally {
      setEnrollingId(null);
    }
  };

  if (loading) return (
    <div className="main-viewport">
      <div className="glass-card">Loading course catalog...</div>
    </div>
  );

  return (
    <div className="main-viewport fade-in">
      {/* ---------- Page Header ---------- */}
      <header className="page-header stacked">
        <div className="header-text">
          <h1>Enroll in a Class</h1>
          <p className="subtitle">Use the filters below to find your batch and join your courses.</p>
        </div>
      </header>

      {/* ---------- Filter Section (Glass Card) ---------- */}
      <div className="glass-card mb-8">
        <div className="filters-container-row">
          <div className="filter-input-group">
            <label htmlFor="department-select">Department</label>
            <select 
              id="department-select"
              className="glass-select"
              value={selectedDept} 
              onChange={(e) => { 
                setSelectedDept(e.target.value); 
                setSelectedProgram(""); 
                setSelectedBatch(null); 
              }}
            >
              <option value="">-- Select Department --</option>
              {hierarchy.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>

          <div className="filter-input-group">
            <label htmlFor="program-select">Program</label>
            <select 
              id="program-select"
              className="glass-select"
              value={selectedProgram} 
              onChange={(e) => { 
                setSelectedProgram(e.target.value); 
                setSelectedBatch(null); 
              }}
              disabled={!selectedDept}
            >
              <option value="">-- Select Program --</option>
              {currentDept?.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* ---------- Batch Selection Tabs ---------- */}
      {currentProgram && (
        <div className="batch-selection-area">
          <p className="section-label">Select Your Batch</p>
          <div className="tabs-flex-row">
            {currentProgram.batches.length > 0 ? (
              currentProgram.batches.map(batch => (
                <button
                  key={batch.id}
                  className={`tab-pill ${selectedBatch?.id === batch.id ? "active" : ""}`}
                  onClick={() => setSelectedBatch(batch)}
                >
                  {batch.name}
                </button>
              ))
            ) : (
              <p className="empty-text">No batches found for this program.</p>
            )}
          </div>
        </div>
      )}

      {/* ---------- Results Area ---------- */}
      <div className="enroll-results-grid">
        {selectedBatch ? (
          selectedBatch.semesters.map(sem => (
            <div key={sem.id} className="semester-block">
              {/* Fixed "7" issue: Clearly labeling as Semester */}
              <div className="semester-header-row">
                <h3 className="semester-title">Semester {sem.name}</h3>
                <div className="semester-divider"></div>
              </div>
              
              <div className="course-grid">
                {sem.sections && sem.sections.length > 0 ? (
                  sem.sections.map(section => (
                    <div key={section.id} className="glass-card course-card enroll-card">
                      <div className="card-badge-row">
                        <span className="tag-badge blue">{section.course_code}</span>
                      </div>
                      
                      <div className="enroll-card-body">
                        <h3>{section.course_title}</h3>
                        <div className="enroll-details">
                          <p><span>Section:</span> {section.section_name}</p>
                          <p><span>Instructor:</span> {section.instructor_name}</p>
                        </div>
                      </div>

                      <div className="enroll-action-box">
                        <input 
                          type="text" 
                          placeholder="Enroll Code"
                          className="glass-input-small"
                          value={enrollmentCodes[section.id] || ""}
                          onChange={(e) => setEnrollmentCodes({
                            ...enrollmentCodes, 
                            [section.id]: e.target.value.toUpperCase()
                          })}
                        />
                        <button 
                          className="join-btn"
                          onClick={() => handleJoinClass(section.id)}
                          disabled={enrollingId === section.id}
                        >
                          {enrollingId === section.id ? "..." : "Join"}
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-state-glass">
                    <p>No classes registered for this semester yet.</p>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state-glass large">
            <div className="empty-icon">🔍</div>
            <p>Please select your Department, Program, and Batch above to view available classes.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseEnroll;
