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

      // Django returns { data: serializer } where `ai_result_json` holds the grading payload
      const data = res?.data?.data;
      if (Array.isArray(data)) {
        setResults(data);
        const ids = data.map((d) => d?.id).filter(Boolean);
        if (ids.length > 0) {
          localStorage.setItem("grading_submission_ids", JSON.stringify(ids));
          localStorage.setItem("grading_submission_id", ids[ids.length - 1]);
        }
      } else {
        const submissionId = data?.id;
        if (submissionId) {
          localStorage.setItem("grading_submission_id", submissionId);
          localStorage.removeItem("grading_submission_ids");
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
      <h1 className="page-title">AI Assessment Grading</h1>

      <form className="assessment-form" onSubmit={handleGrade}>
        <div className="card-section card-purple">
          <label className="section-label">Upload Documents</label>
          <div className="grid-row">
            <div className="upload-group" style={{ flex: 1 }}>
              <label className="sub-label">Student Submission (PDF/DOCX/ZIP)</label>
              <input
                type="file"
                accept=".pdf,.docx,.zip"
                onChange={(e) => setStudentFile(e.target.files[0])}
                className="input-field"
                required
              />
            </div>

            <div className="upload-group" style={{ flex: 1 }}>
              <label className="sub-label">Rubric / Marking Scheme (PDF)</label>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setRubricFile(e.target.files[0])}
                className="input-field"
              />
            </div>
          </div>
        </div>

        <button type="submit" className={`generate-btn ${loading ? "disabled" : ""}`} disabled={loading}>
          {loading ? "Grading..." : "Start Grading"}
        </button>
      </form>

      {error && <p className="error-msg">{error}</p>}

      {/* NEW: Updated Results Display with Metadata and CSV Download */}
      {result && (
        <div className="assessment-result fade-in">
          
          <div className="result-header-main">
            <div className="student-info-panel">
              <h2>Grading Results</h2>
              <p className="cms-text"><strong>Name:</strong> {result.student_name || "Unknown"}</p>
              <p className="cms-text"><strong>CMS ID:</strong> {result.cms_id || "Unknown"}</p>
            </div>
            
            <div className="action-panel">
              {/* CSV Download Button */}
              <a 
                href={`${import.meta.env.VITE_API_BASE_URL || ""}${result.download_url || ""}`} 
                className="download-csv-btn"
                target="_blank" 
                rel="noopener noreferrer"
                download
              >
                <span>Download CSV Report</span>
              </a>
              
              <div className="score-summary-badge">
                Total: {result.summary?.total_obtained ?? 0} / {result.summary?.total_possible ?? 0} ({result.summary?.percentage ?? 0}%)
              </div>
            </div>
          </div>

          <div className="questions-grid">
            {Object.entries(result.per_question || {}).map(([qid, data]) => (
              <div key={qid} className="card-section question-card">
                <div className="q-header">
                  <span className="q-badge">{qid}</span>
                  <span className={`marks-badge ${data.marks_awarded === data.max_marks ? 'full-marks' : 'partial-marks'}`}>
                    {data.marks_awarded} / {data.max_marks} Marks
                  </span>
                </div>
                
                <div className="q-body">
                  <p className="q-text"><strong>Question:</strong> {data.question}</p>
                  
                  <div className="student-answer-box">
                    <span className="label">Student Answer:</span>
                    <p>{data.student_answer || "No answer text detected."}</p>
                  </div>

                  <div className="feedback-box">
                    <span className="label">AI Feedback:</span>
                    <p>{data.feedback}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="assessment-result fade-in">
          <div className="result-header-main">
            <div className="student-info-panel">
              <h2>Bulk Grading Results</h2>
              <p className="cms-text"><strong>Students:</strong> {results.length}</p>
            </div>
          </div>

          <div className="questions-grid">
            {results.map((item) => {
              const payload = item?.ai_result_json || item;
              const key = item?.id || payload?.cms_id || Math.random();
              return (
                <div key={key} className="card-section question-card">
                  <div className="q-header">
                    <span className="q-badge">{payload?.cms_id || "Unknown ID"}</span>
                    <span className="marks-badge">
                      {payload?.summary?.total_obtained ?? 0} / {payload?.summary?.total_possible ?? 0} ({payload?.summary?.percentage ?? 0}%)
                    </span>
                  </div>
                  <div className="q-body">
                    <p className="q-text"><strong>Name:</strong> {payload?.student_name || "Unknown"}</p>
                    {payload?.download_url && (
                      <a
                        href={`${import.meta.env.VITE_API_BASE_URL || ""}${payload.download_url}`}
                        className="download-csv-btn"
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                      >
                        <span>Download CSV Report</span>
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentGrading;
