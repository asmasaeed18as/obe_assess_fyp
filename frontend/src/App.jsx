// src/App.js
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthProvider";

// Import Pages
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import DashboardLayout from "./pages/Dashboard"; 
import DashboardHome from "./pages/DashboardHome"; 
import AssessmentCreate from "./pages/AssessmentCreate";
import AssessmentGrading from "./pages/AssessmentGrading";
import CourseDetail from "./pages/CourseDetail";
import CourseEnroll from "./pages/CourseEnroll"; 
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            
            {/* Dashboard acts as a Layout */}
            <Route path="/dashboard" element={<DashboardLayout />}>
              
              {/* Default Index Route: Shows DashboardHome (Courses) */}
              <Route index element={<DashboardHome />} />
              
              {/* ✅ NEW: Route for creating assessment for a SPECIFIC COURSE */}
              {/* This matches the button in CourseDetail: /dashboard/courses/:id/create-assessment */}
              <Route path="courses/:courseId/create-assessment" element={<AssessmentCreate />} />

              {/* General Route (Fallback if accessing directly without course context) */}
              <Route path="create-assessment" element={<AssessmentCreate />} />
              {/* Grading Page */}
              <Route path="grading" element={<AssessmentGrading />} />
              {/* Course Management Routes */}
              <Route path="courses/:id" element={<CourseDetail />} />
              <Route path="enroll-course" element={<CourseEnroll />} />
              
              {/* Placeholders for future routes */}
              <Route path="grading" element={<div>Grading Page Placeholder</div>} />
              <Route path="analytics" element={<div>Analytics Page Placeholder</div>} />
              <Route path="settings" element={<div>Settings Page Placeholder</div>} />
              
            </Route>

            <Route path="/profile" element={<Profile />} />
          </Route>

          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Fallback */}
          <Route path="*" element={<div>Page not found</div>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;