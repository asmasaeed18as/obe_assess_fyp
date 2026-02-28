import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import api from "../api/axios";
import "../styles/AssessmentCreate.css";

const AssessmentCreate = () => {
  const { courseId: paramCourseId } = useParams();
  const fileInputRef = useRef(null);

  const [selectedCourseId, setSelectedCourseId] = useState(paramCourseId || "");
  const [coursesList, setCoursesList] = useState([]);
  const [courseTitle, setCourseTitle] = useState("");
  const [assessmentType, setAssessmentType] = useState("");
  const [numQuestions, setNumQuestions] = useState(0);
  const [questionsConfig, setQuestionsConfig] = useState([]);
  const [availableClos, setAvailableClos] = useState([]);

  const [inputMode, setInputMode] = useState("file");
  const [topicInput, setTopicInput] = useState("");
  const [materialFile, setMaterialFile] = useState(null);

  const [loading, setLoading] = useState(false);

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
        console.error(err);
      }
    };
    initData();
  }, [paramCourseId]);

  useEffect(() => {
    const fetchClos = async () => {
      if (!selectedCourseId) return;
      try {
        const res = await api.get(`/courses/${selectedCourseId}/clos/`);
        setAvailableClos(Array.isArray(res.data) ? res.data : []);
      } catch {
        setAvailableClos([]);
      }
    };
    fetchClos();
  }, [selectedCourseId]);

  const handleNumQuestionsChange = (e) => {
    const count = parseInt(e.target.value) || 0;
    setNumQuestions(count);

    const newConfig = Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      clo: "",
      difficulty: "Medium",
      weightage: "5",
    }));

    setQuestionsConfig(newConfig);
  };

  const handleQuestionConfigChange = (index, field, value) => {
    const updated = [...questionsConfig];
    updated[index][field] = value;
    setQuestionsConfig(updated);
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setMaterialFile(e.target.files[0]);
      setInputMode("file");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => setLoading(false), 1500);
  };

  return (
    <div className="assessment-container">
      <h1 className="page-title">AI-Powered Assessment Generator</h1>

      <form className="assessment-form" onSubmit={handleSubmit}>
        <div className="workspace-wrapper">
          
          {/* LEFT COLUMN */}
          <div className="form-column">

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
                  <option value="Quiz">Quiz</option>
                  <option value="Assignment">Assignment</option>
                  <option value="Exam">Exam</option>
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
                  onClick={() => fileInputRef.current.click()}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    hidden
                  />
                  {materialFile
                    ? `✓ ${materialFile.name}`
                    : "Click to upload material"}
                </div>
              ) : (
                <textarea
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  className="input-field topic-textarea"
                  placeholder="Enter topic or instructions..."
                />
              )}
            </div>
          </div>

          {/* RIGHT COLUMN */}
          {questionsConfig.length > 0 && (
            <div className="form-column">
              <div className="card-section">
                <label className="section-label">Question Setup</label>
                <div className="questions-list">
                  {questionsConfig.map((q, index) => (
                    <div key={index} className="question-row">
                      <span className="q-index">Q{index + 1}</span>

                      <select
                        value={q.clo}
                        onChange={(e) =>
                          handleQuestionConfigChange(index, "clo", e.target.value)
                        }
                        className="input-field small"
                        required
                      >
                        <option value="">CLO</option>
                        {availableClos.map(clo => (
                          <option key={clo.id} value={clo.code}>
                            {clo.code}
                          </option>
                        ))}
                      </select>

                      <select
                        value={q.difficulty}
                        onChange={(e) =>
                          handleQuestionConfigChange(index, "difficulty", e.target.value)
                        }
                        className="input-field small"
                      >
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                      </select>

                      <input
                        type="number"
                        value={q.weightage}
                        onChange={(e) =>
                          handleQuestionConfigChange(index, "weightage", e.target.value)
                        }
                        className="input-field small"
                        placeholder="Marks"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="action-bar">
          <button
            type="submit"
            className="generate-btn"
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Assessment"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AssessmentCreate;