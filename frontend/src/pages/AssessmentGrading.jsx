import React, { useState } from "react";
import api from "../api/axios";
import "../styles/AssessmentCreate.css"; // Reuse existing styles
import "../styles/AssessmentGrading.css"; // New specific styles for results

const AssessmentGrading = () => {
  const [studentFile, setStudentFile] = useState(null);
  const [rubricFile, setRubricFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleGrade = async (e) => {
    e.preventDefault();
    if (!studentFile || !rubricFile) {
      setError("Please upload both the student submission and the rubric.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("student_file", studentFile);
    formData.append("rubric_file", rubricFile);

    try {
      // Calls the Django Endpoint we created earlier
      const res = await api.post("/grading/grade/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // The backend returns { status: "success", data: { ... } }
      setResult(res.data.data); 
    } catch (err) {
      console.error("Grading failed:", err);
      setError("Failed to grade assessment. Please check your files and try again.");
    } finally {
      setLoading(false);
    }
  };

  // Helper: Calculate total marks awarded
  const calculateTotal = (aiJson) => {
    if (!aiJson?.per_question) return 0;
    return Object.values(aiJson.per_question).reduce((acc, q) => acc + (q.marks_awarded || 0), 0);
  };

  return (
    <div className="assessment-container">
      <h1 className="page-title">AI Assessment Grading</h1>

      <form className="assessment-form" onSubmit={handleGrade}>
        
        {/* Upload Section - Styled like AssessmentCreate */}
        <div className="card-section card-purple">
          <label className="section-label">Upload Documents</label>
          
          <div className="grid-row">
            {/* Student File */}
            <div className="upload-group" style={{ flex: 1 }}>
              <label className="sub-label">Student Submission (PDF)</label>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setStudentFile(e.target.files[0])}
                className="input-field"
                style={{ padding: "10px" }}
                required
              />
            </div>

            {/* Rubric File */}
            <div className="upload-group" style={{ flex: 1 }}>
              <label className="sub-label">Rubric / Marking Scheme (PDF)</label>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setRubricFile(e.target.files[0])}
                className="input-field"
                style={{ padding: "10px" }}
                required
              />
            </div>
          </div>
        </div>

        <button type="submit" className={`generate-btn ${loading ? "disabled" : ""}`} disabled={loading}>
          {loading ? "   Grading..." : "Start Grading"}
        </button>
      </form>

      {error && <p className="error-msg">{error}</p>}

      {/* Results Display */}
      {result && result.ai_result_json && (
        <div className="assessment-result fade-in">
          <div className="result-header">
            <h2>Grading Results</h2>
            <div className="score-badge">
              Total Score: {calculateTotal(result.ai_result_json)} / {result.ai_result_json.total_marks || "N/A"}
            </div>
          </div>

          <div className="questions-grid">
            {Object.entries(result.ai_result_json.per_question || {}).map(([qid, data]) => (
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
                    <p>{data.student_answer ? data.student_answer.substring(0, 300) + (data.student_answer.length > 300 ? "..." : "") : "No answer text detected."}</p>
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
    </div>
  );
};

export default AssessmentGrading;