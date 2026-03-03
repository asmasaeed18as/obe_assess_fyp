import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import api from "../api/axios";

const GradingContext = createContext(null);

export const useGrading = () => {
  const ctx = useContext(GradingContext);
  if (!ctx) {
    throw new Error("useGrading must be used within a GradingProvider");
  }
  return ctx;
};

export const GradingProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [results, setResults] = useState([]);

  const activeRequestIdRef = useRef(0);
  const initialLoadDoneRef = useRef(false);

  const persistIds = useCallback((ids) => {
    if (Array.isArray(ids) && ids.length > 0) {
      localStorage.setItem("grading_submission_ids", JSON.stringify(ids));
      localStorage.setItem("grading_submission_id", ids[ids.length - 1]);
    }
  }, []);

  const clearIds = useCallback(() => {
    localStorage.removeItem("grading_submission_id");
    localStorage.removeItem("grading_submission_ids");
  }, []);

  const grade = useCallback(async ({ studentFile, rubricFile, courseId }) => {
    const requestId = Date.now();
    activeRequestIdRef.current = requestId;

    setLoading(true);
    setError("");
    setResult(null);
    setResults([]);

    const formData = new FormData();
    formData.append("student_file", studentFile);
    if (rubricFile) {
      formData.append("rubric_file", rubricFile);
    }
    if (courseId) {
      formData.append("course_id", courseId);
      localStorage.setItem("grading_course_id", courseId);
    }

    try {
      const res = await api.post("/grading/grade/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (activeRequestIdRef.current !== requestId) {
        return;
      }

      const data = res?.data?.data;
      if (Array.isArray(data)) {
        setResults(data);
        persistIds(data.map((d) => d?.id).filter(Boolean));
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
      if (activeRequestIdRef.current !== requestId) {
        return;
      }
      console.error("Grading failed:", err);
      setError("Failed to grade assessment. Please check your files and try again.");
    } finally {
      if (activeRequestIdRef.current === requestId) {
        setLoading(false);
      }
    }
  }, [persistIds]);

  const reset = useCallback(() => {
    activeRequestIdRef.current = 0;
    setResult(null);
    setResults([]);
    setError("");
    setLoading(false);
    clearIds();
    localStorage.removeItem("grading_course_id");
  }, [clearIds]);

  const loadLastResult = useCallback(async () => {
    if (loading) return;
    const submissionId = localStorage.getItem("grading_submission_id");
    if (!submissionId) return;

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
  }, [loading]);

  useEffect(() => {
    if (initialLoadDoneRef.current) return;
    initialLoadDoneRef.current = true;
    loadLastResult();
  }, [loadLastResult]);

  return (
    <GradingContext.Provider
      value={{
        loading,
        error,
        result,
        results,
        grade,
        reset,
        loadLastResult,
      }}
    >
      {children}
    </GradingContext.Provider>
  );
};

export default GradingContext;
