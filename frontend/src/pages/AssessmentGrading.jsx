import React, { useEffect, useState } from "react";
import api from "../api/axios";
import "../styles/AssessmentCreate.css"; 
import "../styles/AssessmentGrading.css"; 

const AssessmentGrading = () => {
  const [studentFile, setStudentFile] = useState(null);
  const [rubricFile, setRubricFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const handleGrade = async (e) => {
    e.preventDefault();
    if (!studentFile) {
      setError("Please upload the student submission (or ZIP for bulk grading).");
      return;
    }
    const isZip = studentFile?.name?.toLowerCase().endsWith(".zip");
    if (!isZip && !rubricFile) {
      setError("Please upload both the student submission and the rubric.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setResults([]);

    const formData = new FormData();
    formData.append("student_file", studentFile);
    if (rubricFile) {
      formData.append("rubric_file", rubricFile);
    }

    try {
      const res = await api.post("/grading/grade/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = res?.data?.data;
      if (Array.isArray(data)) {
        setResults(data);
        const firstId = data?.[0]?.id;
        if (firstId) {
          localStorage.setItem("grading_submission_id", firstId);
        }
      } else {
        const submissionId = data?.id;
        if (submissionId) {
          localStorage.setItem("grading_submission_id", submissionId);
        }
        const payload = data?.ai_result_json || data;
        setResult(payload || null);
      }
    } catch (err) {
      console.error("Grading failed:", err);
      setError("Failed to grade assessment. Please check your files and try again.");
    } finally {
      setLoading(false);
    }
  };

  // Function to clear results and show the upload button again
  const handleReset = () => {
    setResult(null);
    setResults([]);
    setStudentFile(null);
    setRubricFile(null);
    localStorage.removeItem("grading_submission_id");
  };

  useEffect(() => {
    const submissionId = localStorage.getItem("grading_submission_id");
    if (!submissionId) return;

    const loadLastResult = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/grading/grade/${submissionId}/`);
        const payload = res?.data?.ai_result_json || res?.data?.data?.ai_result_json || res?.data?.data;
        setResult(payload || null);
      } catch (err) {
        console.error("Failed to load last grading result:", err);
        localStorage.removeItem("grading_submission_id");
      } finally {
        setLoading(false);
      }
    };

    loadLastResult();
  }, []);

  return (
    <div className="assessment-container">
      <header className="page-header">
        <h1 className="page-title">AI Assessment Grading</h1>
        <p className="page-subtitle">Upload submissions and rubrics for automated OBE evaluation</p>
      </header>

      {/* Only show the form if no result exists */}
      {!result && results.length === 0 && (
        <form className="assessment-form" onSubmit={handleGrade}>
          <div className="card-section">
            <label className="section-label">Upload Documents</label>
            <div className="upload-grid-row">
              <div className="upload-wrapper">
                <label className="sub-label">Student Submission (PDF/DOCX/ZIP)</label>
                <label className="custom-file-upload">
                  <input
                    type="file"
                    accept=".pdf,.docx,.zip"
                    onChange={(e) => setStudentFile(e.target.files[0])}
                    required
                  />
                  <span className="file-name-display">
                    {studentFile ? studentFile.name : "Click to select student files"}
                  </span>
                </label>
              </div>

              <div className="upload-wrapper">
                <label className="sub-label">Rubric / Marking Scheme (PDF)</label>
                <label className="custom-file-upload">
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={(e) => setRubricFile(e.target.files[0])}
                  />
                  <span className="file-name-display">
                    {rubricFile ? rubricFile.name : "Click to select marking scheme"}
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div className="action-bar-centered">
            <button type="submit" className={`generate-btn ${loading ? "disabled" : ""}`} disabled={loading}>
              {loading ? "Grading..." : "Start Grading"}
            </button>
          </div>
        </form>
      )}

      {error && <p className="error-msg-toast">{error}</p>}

      {/* Results Rendering - Single Student */}
      {result && (
        <div className="assessment-result fade-in">
          <div className="result-header-glass">
            <div className="student-info-panel">
              <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <h2>Grading Results</h2>
                {/* Reset Button to go back to upload mode */}
                <button onClick={handleReset} className="action-pill-glass" style={{ fontSize: '0.7rem', padding: '5px 10px' }}>
                  Grade New +
                </button>
              </div>
              <div className="meta-info">
                <span><strong>Name:</strong> {result.student_name || "Unknown"}</span>
                <span><strong>CMS ID:</strong> {result.cms_id || "Unknown"}</span>
              </div>
            </div>
            
            <div className="action-panel">
              <a 
                href={`${import.meta.env.VITE_API_BASE_URL || ""}${result.download_url || ""}`} 
                className="action-pill-glass"
                target="_blank" 
                rel="noopener noreferrer"
              >
                Download CSV
              </a>
              <div className="score-summary-badge">
                {result.summary?.total_obtained ?? 0} / {result.summary?.total_possible ?? 0}
              </div>
            </div>
          </div>

          <div className="results-grid">
            {Object.entries(result.per_question || {}).map(([qid, data]) => (
              <div key={qid} className="card-section question-card-glass">
                <div className="q-header-row">
                  <span className="q-badge">{qid}</span>
                  <span className={`marks-badge ${data.marks_awarded === data.max_marks ? 'full-marks' : 'partial-marks'}`}>
                    {data.marks_awarded} / {data.max_marks} Marks
                  </span>
                </div>
                
                <div className="q-body-content">
                  <p className="q-text-title"><strong>Question:</strong> {data.question}</p>
                  <div className="answer-feedback-stack">
                    <div className="student-answer-box-glass">
                      <span className="label-tiny">Student Answer:</span>
                      <p>{data.student_answer || "No answer text detected."}</p>
                    </div>
                    <div className="feedback-box-glass">
                      <span className="label-tiny">AI Feedback:</span>
                      <p>{data.feedback}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentGrading;
