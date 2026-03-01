// src/App.js
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthProvider";
import { GradingProvider } from "./contexts/GradingContext";

// Import Pages
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import DashboardLayout from "./pages/Dashboard"; 
import DashboardHome from "./pages/DashboardHome"; 
import AssessmentCreate from "./pages/AssessmentCreate";
import AssessmentGrading from "./pages/AssessmentGrading";
import AssessmentAnalytics from "./pages/AssessmentAnalytics";
import Settings from './pages/Settings';
import CourseDetail from "./pages/CourseDetail";
import CourseEnroll from "./pages/CourseEnroll"; 
import AdminView from "./components/AdminView";

// Route Protectors
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute"; // ✅ Import our new protector

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <GradingProvider>
          <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          {/* Removed /register because only Admins can do that now! */}

          {/* Protected Routes (Must be logged in) */}
          <Route element={<ProtectedRoute />}>
            
            {/* Dashboard acts as a Layout */}
            <Route path="/dashboard" element={<DashboardLayout />}>
              
              {/* Default Index Route: Everyone can see their courses */}
              <Route index element={<DashboardHome />} />
              
              {/* Course Detail: Everyone can view course details */}
              <Route path="courses/:id" element={<CourseDetail />} />

              {/* Settings: Everyone has settings */}
              <Route path="settings" element={<Settings />} />

              {/* ==========================================
                  ROLE-SPECIFIC ROUTES
                  ========================================== */}

              {/* 🛑 ADMIN ONLY */}
              <Route element={<RoleRoute allowedRoles={['admin']} />}>
                <Route path="admin" element={<AdminView />} />
              </Route>

              {/* 🛑 INSTRUCTOR & ADMIN ONLY (Students cannot create/grade assessments) */}
              <Route element={<RoleRoute allowedRoles={['instructor', 'admin']} />}>
                <Route path="courses/:courseId/create-assessment" element={<AssessmentCreate />} />
                <Route path="create-assessment" element={<AssessmentCreate />} />
                <Route path="grading" element={<AssessmentGrading />} />
                <Route path="analytics" element={<AssessmentAnalytics />} />
              </Route>

              {/* 🛑 STUDENT ONLY (Instructors don't enroll in courses, Admins assign them) */}
              <Route element={<RoleRoute allowedRoles={['student']} />}>
                <Route path="enroll-course" element={<CourseEnroll />} />
              </Route>

            </Route>

            {/* Profile Route */}
            <Route path="profile" element={<Profile />} />
          </Route>

          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Fallback */}
          <Route path="*" element={<div>Page not found</div>} />
          </Routes>
        </GradingProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;