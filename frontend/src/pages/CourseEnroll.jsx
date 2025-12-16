import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios"; // Your configured axios instance
import "../styles/Dashboard.css";

const CourseEnroll = () => {
  const navigate = useNavigate();
  
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrollingId, setEnrollingId] = useState(null);

  // 1. Fetch Available Courses
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        // GET /api/courses/
        const response = await api.get("/courses/");
        setCourses(response.data);
      } catch (err) {
        console.error("Failed to load courses:", err);
        setError("Unable to load course list. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  // 2. Handle Enroll Click
  const handleEnroll = async (courseId, courseCode) => {
    setEnrollingId(courseId);
    try {
      // POST /api/courses/{id}/enroll/
      // We send role="student" by default, or you can check user role in context
      await api.post(`/courses/${courseId}/enroll/`, { role: "student" });
      
      alert(`Successfully enrolled in ${courseCode}!`);
      navigate("/dashboard"); // Go back to dashboard to see the new course
    } catch (err) {
      console.error("Enrollment failed:", err);
      // Check if backend returned a specific error message
      const msg = err.response?.data?.detail || "Failed to enroll. You might already be enrolled.";
      alert(msg);
    } finally {
      setEnrollingId(null);
    }
  };

  if (loading) return <div className="p-8">Loading available courses...</div>;

  return (
    <div className="course-enroll-container fade-in">
      <h2 className="page-heading">Enroll in New Course</h2>
      <p className="page-subheading">Select a course from the list below to add it to your dashboard.</p>

      {error && <p className="error-msg">{error}</p>}

      <div className="enroll-grid">
        {courses.length > 0 ? (
          courses.map((course) => (
            <div key={course.id} className="enroll-card">
              <div className="enroll-card-header">
                <h3>{course.title}</h3>
                <span className="course-code-badge">{course.code}</span>
              </div>
              
              <div className="enroll-details">
                <p>{course.description ? course.description.substring(0, 80) + "..." : "No description available."}</p>
              </div>
              
              <button 
                className="enroll-btn-action"
                onClick={() => handleEnroll(course.id, course.code)}
                disabled={enrollingId === course.id}
                style={{ opacity: enrollingId === course.id ? 0.7 : 1 }}
              >
                {enrollingId === course.id ? "Enrolling..." : "Enroll Now"}
              </button>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center text-gray-500 mt-10">
            <p>No courses available for enrollment right now.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseEnroll;