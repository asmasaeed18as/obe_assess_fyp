import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import "../styles/Dashboard.css"; // Ensure this has your card styles

const CourseEnroll = () => {
  const navigate = useNavigate();

  // --- States ---
  const [hierarchy, setHierarchy] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Hierarchy Selection States
  const [selectedDept, setSelectedDept] = useState("");
  const [selectedProgram, setSelectedProgram] = useState("");
  const [selectedBatch, setSelectedBatch] = useState(null);

  // Enrollment Code State (maps section ID to the code entered by the user)
  const [enrollmentCodes, setEnrollmentCodes] = useState({});
  const [enrollingId, setEnrollingId] = useState(null);

  // 1. Fetch Hierarchy Data on Load
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

  // --- Helper to get currently selected data ---
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
      // Calls the JoinSectionView in your Django backend
      const res = await api.post("/join/", { enrollment_code: code });
      alert(`✅ Success: ${res.data.message}`);
      navigate("/dashboard"); // Redirect back to student dashboard
    } catch (err) {
      // Smart error handling!
      const errorMessage = err.response?.data?.error || "Failed to join class. Please check the code and try again.";
      alert(`❌ ${errorMessage}`);
    } finally {
      setEnrollingId(null);
    }
  };

  if (loading) return <div className="p-8">Loading course catalog...</div>;

  return (
    <div className="course-enroll-container fade-in p-6">
      <h2 className="text-2xl font-bold mb-2">Enroll in a Class</h2>
      <p className="text-gray-600 mb-6">Use the filters below to find your batch and enter the enrollment code to join.</p>

      {/* === TOP FILTERS === */}
      <div className="filters-bar" style={{ display: 'flex', gap: '20px', marginBottom: '30px', background: '#f8fafc', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <div className="filter-group" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label className="font-semibold text-sm text-gray-700 mb-2">Department</label>
          <select 
            className="p-2 border rounded"
            value={selectedDept} 
            onChange={(e) => { setSelectedDept(e.target.value); setSelectedProgram(""); setSelectedBatch(null); }}
          >
            <option value="">-- Select Department --</option>
            {hierarchy.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>

        <div className="filter-group" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <label className="font-semibold text-sm text-gray-700 mb-2">Program</label>
          <select 
            className="p-2 border rounded"
            value={selectedProgram} 
            onChange={(e) => { setSelectedProgram(e.target.value); setSelectedBatch(null); }}
            disabled={!selectedDept}
          >
            <option value="">-- Select Program --</option>
            {currentDept?.programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
      </div>

      {/* === BATCH TABS === */}
      {currentProgram && (
        <div className="batch-tabs-row" style={{ display: 'flex', gap: '10px', marginBottom: '30px', overflowX: 'auto' }}>
          {currentProgram.batches.length > 0 ? (
            currentProgram.batches.map(batch => (
              <button
                key={batch.id}
                style={{
                  padding: '8px 16px',
                  borderRadius: '20px',
                  border: selectedBatch?.id === batch.id ? 'none' : '1px solid #cbd5e1',
                  backgroundColor: selectedBatch?.id === batch.id ? '#3b82f6' : 'white',
                  color: selectedBatch?.id === batch.id ? 'white' : '#475569',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
                onClick={() => setSelectedBatch(batch)}
              >
                {batch.name}
              </button>
            ))
          ) : (
            <p className="text-gray-500 italic">No batches found for this program.</p>
          )}
        </div>
      )}

      {/* === CLASS SECTIONS GRID === */}
      <div className="classes-area">
        {selectedBatch ? (
          selectedBatch.semesters.map(sem => (
            <div key={sem.id} className="semester-group mb-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4 border-l-4 border-blue-500 pl-3">{sem.name}</h3>
              
              <div className="course-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                {sem.sections && sem.sections.length > 0 ? (
                  sem.sections.map(section => (
                    <div key={section.id} className="course-card" style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '20px', background: 'white', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
                      
                      <div className="flex justify-between items-start mb-2">
                        <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">{section.course_code}</span>
                      </div>
                      
                      <h4 className="text-lg font-bold text-gray-900 mb-1">{section.course_title}</h4>
                      <p className="text-sm text-gray-600 mb-4">
                        <strong>Sec:</strong> {section.section_name} <br/>
                        <strong>Instructor:</strong> {section.instructor_name}
                      </p>

                      {/* ENROLLMENT ACTION AREA */}
                      <div className="enrollment-action bg-gray-50 p-3 rounded border border-dashed border-gray-300">
                        <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Enrollment Code</label>
                        <div className="flex gap-2">
                          <input 
                            type="text" 
                            placeholder="e.g. A1B2C3"
                            className="w-full p-2 border rounded text-sm uppercase"
                            value={enrollmentCodes[section.id] || ""}
                            onChange={(e) => setEnrollmentCodes({...enrollmentCodes, [section.id]: e.target.value.toUpperCase()})}
                          />
                          <button 
                            className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm transition-colors"
                            onClick={() => handleJoinClass(section.id)}
                            disabled={enrollingId === section.id}
                          >
                            {enrollingId === section.id ? "..." : "Join"}
                          </button>
                        </div>
                      </div>

                    </div>
                  ))
                ) : (
                  <div className="col-span-full text-center text-gray-500 p-8 bg-gray-50 rounded border border-dashed">
                    No classes registered for this semester yet.
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center text-gray-500 p-12 bg-gray-50 rounded-xl border border-dashed">
            Please select your Department, Program, and Batch above to view available classes.
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseEnroll;