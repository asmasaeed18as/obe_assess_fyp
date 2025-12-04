import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "../src/contexts/AuthProvider";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import Dashboard from "./pages/Dashboard";
import AssessmentCreate from "./pages/AssessmentCreate"; // ✅ Import the new page
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes (no login required) */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/create-assessment" element={<AssessmentCreate />} /> {/* ✅ Unprotected route */}

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/profile" element={<Profile />} />
          </Route>

          {/* Fallback route */}
          <Route path="*" element={<div>its just path with no route</div>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
