import React, { useState, useContext } from "react";
import AuthContext  from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import "../styles/Auth.css";


export default function Register() {
  const { register } = useContext(AuthContext);
  const [form, setForm] = useState({ email: "", password: "", username: "", role: "instructor" });
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(form);
      alert("Registered. Please login.");
      navigate("/login");
    } catch (err) {
      setError(err.response?.data || "Registration failed");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Register</h2>
      <input value={form.email} onChange={e => setForm({...form, email:e.target.value})} placeholder="Email" required />
      <input value={form.username} onChange={e => setForm({...form, username:e.target.value})} placeholder="Username" />
      <select value={form.role} onChange={e => setForm({...form, role:e.target.value})}>
        <option value="instructor">Instructor</option>
        <option value="student">Student</option>
        <option value="qa">QA</option>
      </select>
      <input type="password" value={form.password} onChange={e => setForm({...form, password:e.target.value})} placeholder="Password" required />
      <button type="submit">Register</button>
      {error && <div style={{color:"red"}}>{JSON.stringify(error)}</div>}
    </form>
  );
}
