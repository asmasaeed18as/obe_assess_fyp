import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import QuestionCard from "../components/QuestionCard";
import "../styles/AssessmentCreate.css";

const AssessmentCreate = () => {
  const { courseId: paramCourseId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // --- STABLE STATES ---
  const [selectedCourseId, setSelectedCourseId] = useState(paramCourseId || "");
  const [coursesList, setCoursesList] = useState([]);
  const [courseTitle, setCourseTitle] = useState("");

  const [assessmentType, setAssessmentType] = useState("");
  const [numQuestions, setNumQuestions] = useState(0);
  const [questionsConfig, setQuestionsConfig] = useState([]);
  const [availableClos, setAvailableClos] = useState([]);

  // Source Material States
  const [inputMode, setInputMode] = useState("file"); 
  const [topicInput, setTopicInput] = useState("");
  const [outlineFile, setOutlineFile] = useState(null);
  const [materialFile, setMaterialFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [assessment, setAssessment] = useState(null);
  const [error, setError] = useState("");

  const backendBaseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

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
    const fetchClos = async () => {
      if (!selectedCourseId) return;
      try {
        const res = await api.get(`/courses/${selectedCourseId}/clos/`);
        let closData = Array.isArray(res.data) ? res.data : (res.data.results || []);
        setAvailableClos(closData);
      } catch (err) {
        setAvailableClos([]);
      }
    };
    fetchClos();
  }, [selectedCourseId]);

  // --- HANDLERS ---
  const handleNumQuestionsChange = (e) => {
    const count = parseInt(e.target.value) || 0;
    setNumQuestions(count);
    
    const newConfig = Array.from({ length: count }, (_, i) => ({
      id: i + 1, 
      clo: "", 
      bloom_level: "", 
      difficulty: "Medium", 
      weightage: "5",
      question_type: assessmentType === "Quiz/MCQs" ? "MCQ" : "Standard",
      ...(questionsConfig[i] || {})
    }));
    setQuestionsConfig(newConfig);
  };

  const handleQuestionConfigChange = (index, field, value) => {
    const updatedConfig = [...questionsConfig];
    updatedConfig[index][field] = value;
    
    // Auto-fill Bloom Level when CLO is selected
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
    if (!selectedCourseId) { setError("Please select a course first."); return; }
    if (inputMode === "file" && !materialFile) { setError("Please upload a material file."); return; }
    if (inputMode === "topic" && !topicInput.trim()) { setError("Please enter a topic."); return; }

    setLoading(true);
    setError("");
    setAssessment(null);

    try {
      const form = new FormData();
      form.append("course_id", selectedCourseId);
      form.append("assessment_type", assessmentType);
      form.append("questions_config", JSON.stringify(questionsConfig));
      if (outlineFile) form.append("outline", outlineFile);

      if (inputMode === "file") form.append("file", materialFile);
      else form.append("topic_input", topicInput);

      const res = await api.post("/assessment/generate/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setAssessment(res.data);
    } catch (err) {
      console.error("❌ Error generating assessment:", err);
      setError(err.response?.data?.error || "Failed to generate assessment.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadZip = () => {
    if (!assessment?.id) return;
    window.open(`${backendBaseURL}/api/assessment/download-zip/${assessment.id}/docx/`, "_blank");
  };

  return (
    <div className="assessment-container">
      <h1 className="page-title">AI-Powered Assessment Generator</h1>

      <form className="assessment-form" onSubmit={handleSubmit}>
        
        {/* TOP SECTION: Stacked vertically */}
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
              placeholder="Questions"
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
              className={`tab-btn ${inputMode === 'file' ? 'active' : ''}`}
            >
              Upload File
            </button>
            <button
              type="button"
              onClick={() => setInputMode("topic")}
              className={`tab-btn ${inputMode === 'topic' ? 'active' : ''}`}
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
                  <span className="upload-icon">✅</span>
                  <p className="upload-main-text">{materialFile.name}</p>
                  <p className="upload-sub-text">Click to change file</p>
                </div>
              ) : (
                <div className="upload-content">
                  <span className="upload-icon">📁</span>
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

        {/* BOTTOM SECTION: Full Width Question Setup */}
        {questionsConfig.length > 0 && (
          <div className="card-section">
            <label className="section-label">Question Setup</label>
            <div className="questions-list">
              {questionsConfig.map((q, index) => (
                <div key={index} className="question-row" style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '15px' }}>
                  <span className="q-index" style={{ fontWeight: 'bold', color: '#7c3aed' }}>Q{index + 1}</span>

                  {assessmentType === "Quiz/MCQs" && (
                    <select 
                      value={q.question_type || "MCQ"} 
                      onChange={(e) => handleQuestionConfigChange(index, "question_type", e.target.value)} 
                      className="input-field"
                      style={{ flex: 1, minWidth: '120px' }}
                    >
                      <option value="MCQ">MCQ</option>
                      <option value="Short Question">Short</option>
                    </select>
                  )}

                  <select
                    value={q.clo}
                    onChange={(e) => handleQuestionConfigChange(index, "clo", e.target.value)}
                    className="input-field"
                    style={{ flex: 2, minWidth: '150px' }}
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
                    style={{ flex: 1, minWidth: '100px' }}
                    required
                  >
                    <option value="">Bloom</option>
                    {['C1','C2','C3','C4','C5','C6'].map(lvl => <option key={lvl} value={lvl}>{lvl}</option>)}
                  </select>

                  <select
                    value={q.difficulty}
                    onChange={(e) => handleQuestionConfigChange(index, "difficulty", e.target.value)}
                    className="input-field"
                    style={{ flex: 1, minWidth: '100px' }}
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
                    style={{ flex: 1, minWidth: '80px' }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ERROR MESSAGE & ACTION BAR */}
        {error && <p className="error-msg" style={{textAlign: "center", color: "#ff4d4f"}}>{error}</p>}

        <div className="action-bar" style={{ marginTop: '20px', display: 'flex', justifyContent: 'center' }}>
          <button
            type="submit"
            className="generate-btn"
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Assessment"}
          </button>
        </div>
      </form>

      {/* RESTORED: GENERATED ASSESSMENT VIEW */}
      {assessment && (
        <div className="assessment-result" style={{ marginTop: '40px' }}>
          <div className="result-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ color: '#4c1d95' }}>Generated Assessment</h2>
            <button onClick={handleDownloadZip} className="download-zip-btn">Download Bundle (Zip)</button>
          </div>
          <div className="questions-grid">
            {assessment.result_json?.questions?.map((q, idx) => (
              <QuestionCard key={idx} q={q} idx={idx} handleDownload={() => {}} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentCreate;