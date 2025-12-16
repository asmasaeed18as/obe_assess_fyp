import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import QuestionCard from "../components/QuestionCard";
import "../styles/AssessmentCreate.css";

const AssessmentCreate = () => {
  const { courseId: paramCourseId } = useParams(); // Rename to distinguish from state
  const navigate = useNavigate();

  // State to track the selected course (from URL or manual selection)
  const [selectedCourseId, setSelectedCourseId] = useState(paramCourseId || "");
  const [coursesList, setCoursesList] = useState([]); // List of courses for dropdown

  // General Assessment Info
  const [assessmentType, setAssessmentType] = useState("");
  const [numQuestions, setNumQuestions] = useState(0);

  // Dynamic Questions Configuration
  const [questionsConfig, setQuestionsConfig] = useState([]);

  // Data from Backend
  const [availableClos, setAvailableClos] = useState([]);

  // File States
  const [outlineFile, setOutlineFile] = useState(null);
  const [materialFile, setMaterialFile] = useState(null);

  // UI States
  const [loading, setLoading] = useState(false);
  const [assessment, setAssessment] = useState(null);
  const [error, setError] = useState("");

  const backendBaseURL = "http://127.0.0.1:8000";

  // 1. Fetch List of Courses (If no ID in URL)
  useEffect(() => {
    if (!paramCourseId) {
      const fetchCourses = async () => {
        try {
          const res = await api.get("/courses/");
          setCoursesList(res.data);
        } catch (err) {
          console.error("Failed to load courses list", err);
        }
      };
      fetchCourses();
    } else {
      setSelectedCourseId(paramCourseId);
    }
  }, [paramCourseId]);

  // 2. Fetch CLOs whenever selectedCourseId changes
  useEffect(() => {
    const fetchClos = async () => {
      if (!selectedCourseId) return;
      
      console.log(`🔍 Fetching CLOs for Course ID: ${selectedCourseId}`);
      try {
        const res = await api.get(`/courses/${selectedCourseId}/clos/`);
        
        // Handle Pagination vs Array
        let closData = [];
        if (Array.isArray(res.data)) {
            closData = res.data;
        } else if (res.data && Array.isArray(res.data.results)) {
            closData = res.data.results;
        }

        console.log("✅ CLOs Loaded:", closData);
        setAvailableClos(closData);
      } catch (err) {
        console.error("Failed to fetch CLOs:", err);
        setAvailableClos([]); // Reset if failed
      }
    };
    fetchClos();
  }, [selectedCourseId]);

  // Handle Number of Questions Change
  const handleNumQuestionsChange = (e) => {
    const count = parseInt(e.target.value) || 0;
    setNumQuestions(count);
    const newConfig = Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      clo: "",
      bloom_level: "",
      difficulty: "Medium",
      weightage: "5",
      ...(questionsConfig[i] || {})
    }));
    setQuestionsConfig(newConfig);
  };

  // Handle Changes inside specific Question Rows
  const handleQuestionConfigChange = (index, field, value) => {
    const updatedConfig = [...questionsConfig];
    updatedConfig[index][field] = value;

    if (field === "clo") {
      const selectedClo = availableClos.find(c => c.code === value);
      if (selectedClo && selectedClo.bloom_level) {
        updatedConfig[index]["bloom_level"] = selectedClo.bloom_level;
      }
    }
    setQuestionsConfig(updatedConfig);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCourseId) {
        setError("Please select a course first.");
        return;
    }

    setLoading(true);
    setError("");
    setAssessment(null);

    try {
      const form = new FormData();
      form.append("course_id", selectedCourseId); // ✅ Use state ID
      form.append("assessment_type", assessmentType);
      form.append("questions_config", JSON.stringify(questionsConfig));
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

  const handleDownloadZip = () => {
    if (!assessment?.id) return;
    window.open(`${backendBaseURL}/api/assessment/download-zip/${assessment.id}/docx/`, "_blank");
  };

  return (
    <div className="assessment-container">
      <h1 className="page-title">AI-Powered Assessment Generator</h1>

      <form className="assessment-form" onSubmit={handleSubmit}>
        
        {/* Step 0: Select Course (Only if accessing from Sidebar) */}
        {!paramCourseId && (
            <div className="card-section" style={{ borderLeft: "4px solid #5b5fc7" }}>
                <label className="section-label">Select Course</label>
                <select 
                    className="input-field"
                    value={selectedCourseId}
                    onChange={(e) => setSelectedCourseId(e.target.value)}
                    required
                >
                    <option value="">-- Choose a Course --</option>
                    {coursesList.map(course => (
                        <option key={course.id} value={course.id}>
                            {course.code} - {course.title}
                        </option>
                    ))}
                </select>
            </div>
        )}

        {/* Step 1: Assessment Type */}
        <div className="card-section card-purple">
          <label className="section-label">Assessment Details</label>
          <select
            value={assessmentType}
            onChange={(e) => setAssessmentType(e.target.value)}
            className="input-field"
            required
          >
            <option value="">Select Assessment Type</option>
            <option value="Quiz">Quiz</option>
            <option value="Assignment">Assignment</option>
            <option value="Exam">Exam</option>
            <option value="Project Report">Project Report</option>
          </select>
        </div>

        {/* Step 2: Number of questions */}
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

        {/* Step 3: Question Config Loop */}
        {questionsConfig.length > 0 && (
          <div className="questions-container">
            <h3>Questions Breakdown</h3>
            {questionsConfig.map((q, index) => (
              <div key={index} className="card-section question-config-card">
                <span className="q-badge">Q{index + 1}</span>
                <div className="grid-row">
                  <select
                    value={q.clo}
                    onChange={(e) => handleQuestionConfigChange(index, "clo", e.target.value)}
                    className="input-field"
                    required
                  >
                    <option value="">Select CLO</option>
                    {availableClos.length > 0 ? (
                      availableClos.map((clo) => (
                        <option key={clo.id} value={clo.code}>
                          {clo.code} ({clo.bloom_level || "No Bloom"})
                        </option>
                      ))
                    ) : (
                      <option disabled>No CLOs found (Select a Course & Upload Outline)</option>
                    )}
                  </select>

                  <select
                    value={q.bloom_level}
                    onChange={(e) => handleQuestionConfigChange(index, "bloom_level", e.target.value)}
                    className="input-field"
                    required
                  >
                    <option value="">Bloom Level</option>
                    {['C1','C2','C3','C4','C5','C6'].map(lvl => (
                      <option key={lvl} value={lvl}>{lvl}</option>
                    ))}
                  </select>
                </div>
                
                <div className="grid-row">
                  <select
                    value={q.difficulty}
                    onChange={(e) => handleQuestionConfigChange(index, "difficulty", e.target.value)}
                    className="input-field"
                    required
                  >
                    <option value="">Difficulty</option>
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
                    min="1"
                    required
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Step 4: File Uploads */}
        <div className="card-section card-green">
          <label className="section-label">Course Materials</label>
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
              ⬆ Upload Material
            </button>
            {materialFile && <span className="file-name">{materialFile.name}</span>}
          </div>
        </div>

        <button type="submit" className={`generate-btn ${loading ? "disabled" : ""}`} disabled={loading}>
          {loading ? "Generating..." : "Generate Assessment"}
        </button>
      </form>

      {error && <p className="error-msg">{error}</p>}

      {assessment && (
        <div className="assessment-result">
          <div className="result-header">
            <h2>Generated Assessment</h2>
            <button onClick={handleDownloadZip} className="download-zip-btn">
              📥 Download Bundle (Zip)
            </button>
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