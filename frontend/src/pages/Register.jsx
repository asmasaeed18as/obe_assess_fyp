import React, { useState, useContext } from "react";
import AuthContext from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import "../styles/Auth.css";
import logo from "../assets/obe-logo.png"; 

export default function Register() {
  const { register } = useContext(AuthContext);
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    role: "",
  });
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(form);
      alert("Registered successfully. Please login.");
      navigate("/login");
    } catch (err) {
      setError(err.response?.data || "Registration failed");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <img src={logo} alt="OBE Assess Logo" className="auth-logo" />
          <h2 className="auth-title">Create Account</h2>
          <p className="auth-subtitle">OBE-Assess Platform</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit} autoComplete="off">
          {/* Field 1: Email Address */}
          <input
            type="email"
            name="register_email"
            placeholder="Email Address"
            className="input-field"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />

          {/* Field 2: Username */}
          <input
            type="text"
            name="register_username"
            placeholder="Username"
            className="input-field"
            autoComplete="off"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />

          {/* Field 3: Role Dropdown */}
          <select
            name="register_role"
            className="input-field"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="" disabled hidden>Role</option>
            <option value="instructor">Instructor</option>
            <option value="student">Student</option>
            <option value="qa">QA</option>
          </select>

          {/* Field 4: Password */}
          <input
            type="password"
            name="register_password"
            placeholder="Password"
            className="input-field"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />

          <button type="submit" className="auth-btn">
            Create Account
          </button>
        </form>

        {error && (
          <div className="auth-error">
            {typeof error === 'string' ? error : "Registration failed"}
          </div>
        )}

        <p className="auth-footer">
          Already have an account?{" "}
          <span onClick={() => navigate("/login")}>Login</span>
        </p>
      </div>
    </div>
  );
}