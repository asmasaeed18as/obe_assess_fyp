import React, { useState, useEffect } from "react";
import api from "../api/axios";
import QuestionCard from "../components/QuestionCard";
import "../styles/AssessmentCreate.css";

const AssessmentCreate = () => {
  // General Assessment Info
  const [assessmentType, setAssessmentType] = useState("");
  const [numQuestions, setNumQuestions] = useState(0);

  // Dynamic Questions Configuration (Array of objects)
  const [questionsConfig, setQuestionsConfig] = useState([]);

  // File States
  const [outlineFile, setOutlineFile] = useState(null);
  const [materialFile, setMaterialFile] = useState(null);

  // UI States
  const [loading, setLoading] = useState(false);
  const [assessment, setAssessment] = useState(null);
  const [error, setError] = useState("");

  const backendBaseURL = "http://127.0.0.1:8000";

  // Handle Number of Questions Change -> Generates Rows
  const handleNumQuestionsChange = (e) => {
    const count = parseInt(e.target.value) || 0;
    setNumQuestions(count);

    // Create a new array based on the count, preserving existing data if possible
    const newConfig = Array.from({ length: count }, (_, i) => {
      return (
        questionsConfig[i] || {
          id: i + 1,
          clo: "",
          bloom_level: "",
          difficulty: "",
          weightage: "",
        }
      );
    });
    setQuestionsConfig(newConfig);
  };

  // Handle Changes inside specific Question Rows
  const handleQuestionConfigChange = (index, field, value) => {
    const updatedConfig = [...questionsConfig];
    updatedConfig[index][field] = value;
    setQuestionsConfig(updatedConfig);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setAssessment(null);

    try {
      const form = new FormData();

      // Standard Fields
      form.append("assessment_type", assessmentType);
      
      // We send the list of questions as a JSON string for the backend to parse
      form.append("questions_config", JSON.stringify(questionsConfig));

      // Files
      if (materialFile) form.append("file", materialFile);
      if (outlineFile) form.append("outline", outlineFile);

      const res = await api.post("/assessment/generate/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setAssessment(res.data);
    } catch (err) {
      console.error("❌ Error generating assessment:", err);
      setError("Failed to generate assessment. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (questionId) => {
    if (assessment?.pdf) {
      const fullUrl = assessment.pdf.startsWith("http")
        ? assessment.pdf
        : `${backendBaseURL}${assessment.pdf}`;
      window.open(fullUrl, "_blank");
    } else {
      const question = assessment.result_json.questions.find(
        (q) => q.id === questionId
      );
      if (question?.pdf) {
        const pdfUrl = question.pdf.startsWith("http")
          ? question.pdf
          : `${backendBaseURL}${question.pdf}`;
        window.open(pdfUrl, "_blank");
      } else {
        alert("PDF not available for this question.");
      }
    }
  };

  return (
    <div className="assessment-container">
      <h1 className="page-title">AI-Powered Assessment Generator</h1>

      <form className="assessment-form" onSubmit={handleSubmit}>
        
        {/* ===== Step 1: Assessment Type ===== */}
        <div className="card-section card-purple">
          <label className="section-label">Assessment Details</label>
          <select
            value={assessmentType}
            onChange={(e) => setAssessmentType(e.target.value)}
            className="input-field"
            required
          >
            <option value="">Select Assessment Type</option>
            <option value="quiz">Quiz</option>
            <option value="assignment">Assignment</option>
            <option value="exam">Exam</option>
            <option value="project report">Project Report</option>
          </select>
        </div>

        {/* ===== Step 2: Define Structure (Only shows if type is selected) ===== */}
        {assessmentType && (
          <div className="card-section card-peach">
            <label className="section-label">Number of questions</label>
            <input
              type="number"
              value={numQuestions}
              onChange={handleNumQuestionsChange}
              className="input-field"
              placeholder="Total Number of Questions"
              min="1"
              max="20"
              required
            />
          </div>
        )}

        {/* ===== Step 3: Question Specifics Loop ===== */}
        {questionsConfig.length > 0 && (
          <div className="questions-container">
            <h3>Questions Breakdown</h3>
            {questionsConfig.map((q, index) => (
              <div key={index} className="card-section question-config-card">
                <span className="q-badge">Q{index + 1}</span>
                
                <div className="grid-row">
                  {/* CLO Selection */}
                  <select
                    value={q.clo}
                    onChange={(e) =>
                      handleQuestionConfigChange(index, "clo", e.target.value)
                    }
                    className="input-field"
                    required
                  >
                    <option value="">Select CLO</option>
                    <option value="CLO-1">CLO-1</option>
                    <option value="CLO-2">CLO-2</option>
                    <option value="CLO-3">CLO-3</option>
                    <option value="CLO-4">CLO-4</option>
                  </select>

                  {/* Bloom Level */}
                  <select
                    value={q.bloom_level}
                    onChange={(e) =>
                      handleQuestionConfigChange(index, "bloom_level", e.target.value)
                    }
                    className="input-field"
                    required
                  >
                    <option value="">Bloom Level</option>
                    <option value="C1">C1 - Remember</option>
                    <option value="C2">C2 - Understand</option>
                    <option value="C3">C3 - Apply</option>
                    <option value="C4">C4 - Analyze</option>
                    <option value="C5">C5 - Evaluate</option>
                    <option value="C6">C6 - Create</option>
                  </select>
                </div>

                <div className="grid-row">
                  {/* Difficulty */}
                  <select
                    value={q.difficulty}
                    onChange={(e) =>
                      handleQuestionConfigChange(index, "difficulty", e.target.value)
                    }
                    className="input-field"
                    required
                  >
                    <option value="">Difficulty</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>

                  {/* Weightage */}
                  <input
                    type="number"
                    value={q.weightage}
                    onChange={(e) =>
                      handleQuestionConfigChange(index, "weightage", e.target.value)
                    }
                    className="input-field"
                    placeholder="Marks (e.g. 5)"
                    min="1"
                    required
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ===== Step 4: File Uploads ===== */}
        <div className="card-section card-green">
          <label className="section-label">Course Materials</label>
          
          {/* Outline Upload */}
          <div className="upload-row">
            <input
              type="file"
              id="outline"
              onChange={(e) => setOutlineFile(e.target.files[0])}
              className="input-file"
            />
            <button
              type="button"
              className="upload-btn"
              onClick={() => document.getElementById("outline").click()}
            >
              ⬆ Upload Course Outline
            </button>
            {outlineFile && (
              <span className="file-name">{outlineFile.name}</span>
            )}
          </div>

          {/* Material Upload */}
          <div className="upload-row">
            <input
              type="file"
              id="material"
              onChange={(e) => setMaterialFile(e.target.files[0])}
              className="input-file"
              required
            />
            <button
              type="button"
              className="upload-btn"
              onClick={() => document.getElementById("material").click()}
            >
              ⬆ Upload Relevant Material
            </button>
            {materialFile && (
              <span className="file-name">{materialFile.name}</span>
            )}
          </div>
        </div>

        {/* ===== Submit ===== */}
        <button
          type="submit"
          className={`generate-btn ${loading ? "disabled" : ""}`}
          disabled={loading}
        >
          {loading ? "Generating Assessment..." : "Generate Assessment"}
        </button>
      </form>

      {/* ===== Error Message ===== */}
      {error && <p className="error-msg">{error}</p>}

      {/* ===== Results ===== */}
      {assessment && (
        <div className="assessment-result">
          <h2>Generated Questions</h2>
          {assessment.result_json?.questions?.map((q, idx) => (
            <QuestionCard
              key={idx}
              q={q}
              idx={idx}
              handleDownload={handleDownload}
            />
          ))}

          {assessment.pdf && (
            <button onClick={handleDownload} className="download-link">
              Download Complete PDF
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default AssessmentCreate;