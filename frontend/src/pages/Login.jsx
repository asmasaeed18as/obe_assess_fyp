import React, { useState, useContext } from "react";
import AuthContext from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import "../styles/Login.css";
import logo from "../assets/obe-logo.png";

export default function Login() {
  const { login } = useContext(AuthContext);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
 <div className="login-page">
  <div className="login-card">
    <div className="login-header">
      <img src={logo} alt="OBE-Assess" className="main-logo" />
      <h1 className="brand-name">OBE-Assess</h1>
      <p className="login-subtitle">AI Powered OBE Assessment System</p>
    </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>Email Address</label>
            <input
              type="email"
              placeholder="e.g. professor@university.edu"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={isLoading}>
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        {error && <div className="error-box">{error}</div>}

        <p className="login-footer">
          Forgotten  Your Username or Password?
           {/* <span onClick={() => navigate("/register")}>Register here</span> */}
        </p>
      </div>
    </div>
  );
}
