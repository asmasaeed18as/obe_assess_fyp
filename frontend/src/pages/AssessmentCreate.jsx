import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import "../styles/AssessmentCreate.css";
import {
  subscribeAssessmentGeneration,
  startAssessmentGeneration,
  clearAssessmentGeneration,
  getAssessmentGenerationState,
  hasAssessmentGenerationInFlight,
} from "../utils/assessmentGenerationStore";

const AssessmentCreate = () => {
  const { courseId: paramCourseId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // --- STABLE STATES ---
  const [selectedCourseId, setSelectedCourseId] = useState(paramCourseId || "");
  const [coursesList, setCoursesList] = useState([]);
  const [courseTitle, setCourseTitle] = useState("");

  const [assessmentType, setAssessmentType] = useState("");
  const [numQuestions, setNumQuestions] = useState("");
  const [questionsConfig, setQuestionsConfig] = useState([]);
  const [availableClos, setAvailableClos] = useState([]);

  // Source Material States
  const [inputMode, setInputMode] = useState("file");
  const [topicInput, setTopicInput] = useState("");
  const [outlineFile, setOutlineFile] = useState(null);
  const [materialFile, setMaterialFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [generatedAssessment, setGeneratedAssessment] = useState(null);
  const [generationState, setGenerationState] = useState(getAssessmentGenerationState());

  // --- EFFECTS ---
  useEffect(() => {
    const initData = async () => {
      try {
        if (!paramCourseId) {
          const res = await api.get("/courses/");
          setCoursesList(res.data);
        } else {
          setSelectedCourseId(paramCourseId);
          const res = await api.get(`/courses/${paramCourseId}/`);
          setCourseTitle(res.data.title);
        }
      } catch (err) {
        console.error("Failed to load course data", err);
      }
    };
    initData();
  }, [paramCourseId]);

  useEffect(() => {
    const unsubscribe = subscribeAssessmentGeneration((state) => {
      setGenerationState(state);
      if (state.status === "in_progress") {
        setLoading(true);
        setError("");
        setSuccess("Assessment generation in progress...");
        setGeneratedAssessment(null);
      } else if (state.status === "completed") {
        setLoading(false);
        setError("");
        setSuccess("Assessment generated successfully.");
        if (state.result) {
          setGeneratedAssessment(state.result);
        }
      } else if (state.status === "error") {
        setLoading(false);
        setError(state.error || "Failed to generate assessment.");
        setSuccess("");
      } else {
        setLoading(false);
        setError("");
        setSuccess("");
      }
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const fetchClos = async () => {
      if (!selectedCourseId) return;
      try {
        const res = await api.get(`/courses/${selectedCourseId}/clos/`);
        const closData = Array.isArray(res.data) ? res.data : (res.data.results || []);
        setAvailableClos(closData);
      } catch (err) {
        setAvailableClos([]);
      }
    };
    fetchClos();
  }, [selectedCourseId]);

  // --- HANDLERS ---
  const handleNumQuestionsChange = (e) => {
    const value = e.target.value;
    const count = value ? parseInt(value) : 0;
    setNumQuestions(value); // Keep the raw value (can be empty string)

    const newConfig = Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      clo: "",
      bloom_level: "C1",
      difficulty: "Medium",
      weightage: "5",
      question_type: assessmentType === "Quiz/MCQs" ? "MCQ" : "Standard",
      ...(questionsConfig[i] || {}),
    }));
    setQuestionsConfig(newConfig);
  };

  const handleQuestionConfigChange = (index, field, value) => {
    const updatedConfig = [...questionsConfig];
    updatedConfig[index][field] = value;

    if (field === "clo") {
      const selectedClo = availableClos.find(c => c.code === value);
      if (selectedClo?.bloom_level) updatedConfig[index]["bloom_level"] = selectedClo.bloom_level;
    }
    setQuestionsConfig(updatedConfig);
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setMaterialFile(e.target.files[0]);
      setInputMode("file");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setGeneratedAssessment(null);

    if (!selectedCourseId) {
      setError("Please select a course.");
      return;
    }
    if (!assessmentType) {
      setError("Please select an assessment type.");
      return;
    }
    if (!numQuestions || numQuestions < 1) {
      setError("Please enter number of questions.");
      return;
    }
    if (!questionsConfig.length) {
      setError("Please configure at least one question.");
      return;
    }
    for (let i = 0; i < questionsConfig.length; i += 1) {
      const q = questionsConfig[i];
      if (!q.clo) {
        setError(`Please select CLO for Q${i + 1}.`);
        return;
      }
      if (!q.weightage) {
        setError(`Please enter marks for Q${i + 1}.`);
        return;
      }
    }
    if (inputMode === "file" && !materialFile) {
      setError("Please upload a material file.");
      return;
    }
    if (inputMode === "topic" && !topicInput.trim()) {
      setError("Please enter a topic.");
      return;
    }

    const form = new FormData();
    form.append("course_id", selectedCourseId);
    form.append("assessment_type", assessmentType);
    form.append("questions_config", JSON.stringify(questionsConfig));
    if (outlineFile) {
      form.append("outline", outlineFile);
    }
    if (inputMode === "file") {
      form.append("file", materialFile);
    } else {
      form.append("topic_input", topicInput);
    }

    try {
      await startAssessmentGeneration(form, selectedCourseId);
    } catch (err) {
      console.error("Assessment generation failed:", err);
    }
  };

  const generatedQuestions = generatedAssessment?.result_json?.questions || [];
  const viewCourseId = selectedCourseId || generationState.courseId;

  const handleDownloadZip = async (assessmentId) => {
    try {
      const res = await api.get(`/assessment/download-zip/${assessmentId}/docx/`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `Assessment_Bundle_${assessmentId}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Zip download failed:", err);
    }
  };

  return (
    <div className="assessment-container">
      <h1 className="page-title">AI-Powered Assessment Generator</h1>

      <form className="assessment-form" onSubmit={handleSubmit} noValidate>
        <div className="card-section">
          <label className="section-label">Select Course</label>
          {!paramCourseId ? (
            <select
              className="input-field"
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              required
            >
              <option value="">Choose a Course</option>
              {coursesList.map(course => (
                <option key={course.id} value={course.id}>
                  {course.code} - {course.title}
                </option>
              ))}
            </select>
          ) : (
            <div className="course-display-name">{courseTitle}</div>
          )}
        </div>

        <div className="card-section">
          <label className="section-label">Assessment Details</label>
          <div className="grid-row">
            <select
              value={assessmentType}
              onChange={(e) => setAssessmentType(e.target.value)}
              className="input-field"
              required
            >
              <option value="">Assessment Type</option>
              <option value="Quiz/MCQs">Quiz/MCQs</option>
              <option value="Assignment">Assignment</option>
              <option value="Exam">Exam</option>
              <option value="Project Report">Project Report</option>
              <option value="Lab Manual">Lab Manual</option>
            </select>

            <input
              type="number"
              value={numQuestions}
              onChange={handleNumQuestionsChange}
              className="input-field"
              placeholder="Number of questions"
              min="1"
              max="20"
              required
            />
          </div>
        </div>

        <div className="card-section">
          <label className="section-label">Source Material</label>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            style={{ display: "none" }}
          />

          <div className="source-tabs-wrapper">
            <button
              type="button"
              onClick={() => setInputMode("file")}
              className={`tab-btn ${inputMode === "file" ? "active" : ""}`}
            >
              Upload File
            </button>
            <button
              type="button"
              onClick={() => setInputMode("topic")}
              className={`tab-btn ${inputMode === "topic" ? "active" : ""}`}
            >
              Enter Topic
            </button>
          </div>

          {inputMode === "file" ? (
            <div
              className="file-upload-zone"
              onClick={() => fileInputRef.current?.click()}
            >
              {materialFile ? (
                <div className="upload-content success">
                  <span className="upload-icon">?</span>
                  <p className="upload-main-text">{materialFile.name}</p>
                  <p className="upload-sub-text">Click to change file</p>
                </div>
              ) : (
                <div className="upload-content">
                  <span className="upload-icon">??</span>
                  <p className="upload-main-text">Click here to browse your files</p>
                  <p className="upload-sub-text">Supports PDF, DOCX, and TXT</p>
                </div>
              )}
            </div>
          ) : (
            <textarea
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              className="input-field topic-textarea"
              placeholder="Enter topic or instructions..."
              rows="4"
            />
          )}
        </div>

        {questionsConfig.length > 0 && (
          <div className="card-section">
            <label className="section-label">Question Setup</label>
            <div className="questions-list">
              {questionsConfig.map((q, index) => (
                <div
                  key={index}
                  className="question-row"
                  style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap", marginBottom: "15px" }}
                >
                  <span className="q-index" style={{ fontWeight: "bold", color: "#7c3aed" }}>Q{index + 1}</span>

                  {assessmentType === "Quiz/MCQs" && (
                    <select
                      value={q.question_type || "MCQ"}
                      onChange={(e) => handleQuestionConfigChange(index, "question_type", e.target.value)}
                      className="input-field"
                      style={{ flex: 1, minWidth: "120px" }}
                    >
                      <option value="MCQ">MCQ</option>
                      <option value="Short Question">Short</option>
                    </select>
                  )}

                  <select
                    value={q.clo}
                    onChange={(e) => handleQuestionConfigChange(index, "clo", e.target.value)}
                    className="input-field"
                    style={{ flex: 2, minWidth: "150px" }}
                    required
                  >
                    <option value="">CLO</option>
                    {availableClos.map(clo => (
                      <option key={clo.id} value={clo.code}>
                        {clo.code} ({clo.bloom_level})
                      </option>
                    ))}
                  </select>

                  <select
                    value={q.bloom_level}
                    onChange={(e) => handleQuestionConfigChange(index, "bloom_level", e.target.value)}
                    className="input-field"
                    style={{ flex: 1, minWidth: "100px" }}
                    required
                  >
                    <option value="">Bloom</option>
                    {['C1','C2','C3','C4','C5','C6','P2','P3','P4','P5','P6','P7','A1','A2','A3','A4','A5'].map(lvl => (
                      <option key={lvl} value={lvl}>{lvl}</option>
                    ))}
                  </select>

                  <select
                    value={q.difficulty}
                    onChange={(e) => handleQuestionConfigChange(index, "difficulty", e.target.value)}
                    className="input-field"
                    style={{ flex: 1, minWidth: "100px" }}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>

                  <input
                    type="number"
                    value={q.weightage}
                    onChange={(e) => handleQuestionConfigChange(index, "weightage", e.target.value)}
                    className="input-field"
                    placeholder="Marks"
                    style={{ flex: 1, minWidth: "80px" }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="action-bar" style={{ marginTop: "20px", display: "flex", justifyContent: "center" }}>
          <button
            type="submit"
            className="generate-btn"
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Assessment"}
          </button>
        </div>
      </form>

      {error && <p className="error-msg">{error}</p>}
      {success && <p className="success-msg">{success}</p>}
      {generationState.status === "in_progress" && !hasAssessmentGenerationInFlight() && (
        <p className="error-msg">
          A generation request was in progress, but this page was refreshed. Please check the course assessments or generate again.
        </p>
      )}

      {generatedAssessment && (
        <div className="assessment-form" style={{ marginTop: "20px" }}>
          <div className="card-section">
            <label className="section-label">Generated Assessment</label>
            <div className="action-bar" style={{ justifyContent: "flex-start", gap: "10px" }}>
              <button
                type="button"
                className="generate-btn"
                onClick={() => handleDownloadZip(generatedAssessment.id)}
              >
                Download ZIP
              </button>
              <button
                type="button"
                className="generate-btn"
                onClick={() => viewCourseId && navigate(`/dashboard/courses/${viewCourseId}`)}
                disabled={!viewCourseId}
              >
                View In Course
              </button>
              <button
                type="button"
                className="generate-btn"
                onClick={() => clearAssessmentGeneration()}
              >
                Clear Status
              </button>
            </div>
          </div>

          <div className="card-section">
            <label className="section-label">Questions Preview</label>
            {generatedQuestions.length > 0 ? (
              <div className="questions-list">
                {generatedQuestions.map((q, index) => (
                  <div key={q.id || index} className="question-row" style={{ alignItems: "flex-start" }}>
                    <span className="q-index">Q{index + 1}</span>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", width: "100%" }}>
                      <div>{q.question || "Question text not available."}</div>
                      <div style={{ fontSize: "0.9rem", opacity: 0.8 }}>
                        Marks: {q.marks || "N/A"}{" "}
                        {q.meta?.clo ? `| CLO: ${q.meta.clo}` : ""}
                        {q.meta?.bloom ? ` | Bloom: ${q.meta.bloom}` : ""}
                        {q.meta?.difficulty ? ` | Difficulty: ${q.meta.difficulty}` : ""}
                      </div>
                      {Array.isArray(q.options) && q.options.length > 0 && (
                        <div style={{ fontSize: "0.9rem", opacity: 0.85 }}>
                          {q.options.join("  ")}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state-card">
                <p>No questions returned by the generator.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentCreate;
