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
    /* Force the page to be exactly the height of the screen */
    <div className="auth-page" style={{ height: '100vh', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="auth-card" style={{ padding: '20px', width: '100%', maxWidth: '400px' }}>
        
        {/* Shrink logo and margins */}
        <img src={logo} alt="OBE Assess Logo" className="auth-logo" style={{ height: '50px', marginBottom: '10px' }} />

        <h2 className="auth-title" style={{ margin: '0 0 5px 0', fontSize: '1.5rem' }}>Create Account</h2>
        <p className="auth-subtitle" style={{ marginBottom: '15px' }}>OBE Assessment System</p>

        <form className="auth-form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            type="email"
            placeholder="Email"
            className="input-field"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
            style={{ padding: '10px' }}
          />

          <input
            type="text"
            placeholder="Username"
            className="input-field"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
            style={{ padding: '10px' }}
          />

          <select
            className="input-field"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            style={{ padding: '10px', background: '#fff' }}
          >
            <option value="instructor">Instructor</option>
            <option value="student">Student</option>
            <option value="qa">QA</option>
          </select>

          <input
            type="password"
            placeholder="Password"
            className="input-field"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            style={{ padding: '10px' }}
          />

          <button type="submit" className="auth-btn" style={{ padding: '12px', marginTop: '5px' }}>
            Register
          </button>
        </form>

        {error && (
          <div className="auth-error" style={{ fontSize: '0.8rem', marginTop: '10px', maxHeight: '40px', overflow: 'hidden' }}>
            {typeof error === 'string' ? error : "Registration failed"}
          </div>
        )}

        <p className="auth-footer" style={{ marginTop: '15px', fontSize: '0.9rem' }}>
          Already have an account?{" "}
          <span onClick={() => navigate("/login")} style={{ cursor: 'pointer', fontWeight: 'bold' }}>Login</span>
        </p>
      </div>
    </div>
  );
}