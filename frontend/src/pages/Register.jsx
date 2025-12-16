import React, { useState, useContext } from "react";
import AuthContext from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import "../styles/Auth.css";
import logo from "../assets/obe-logo.png"; // same logo as login

export default function Register() {
  const { register } = useContext(AuthContext);
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    role: "instructor",
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
        <img src={logo} alt="OBE Assess Logo" className="auth-logo" />

        <h2 className="auth-title">Create Account</h2>
        <p className="auth-subtitle">OBE Assessment System</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) =>
              setForm({ ...form, email: e.target.value })
            }
            required
          />

          <input
            type="text"
            placeholder="Username"
            value={form.username}
            onChange={(e) =>
              setForm({ ...form, username: e.target.value })
            }
            required
          />

          <select
            value={form.role}
            onChange={(e) =>
              setForm({ ...form, role: e.target.value })
            }
          >
            <option value="instructor">Instructor</option>
            <option value="student">Student</option>
            <option value="qa">QA</option>
          </select>

          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) =>
              setForm({ ...form, password: e.target.value })
            }
            required
          />

          <button type="submit" className="auth-btn">
            Register
          </button>
        </form>

        {error && (
          <div className="auth-error">
            {JSON.stringify(error)}
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
