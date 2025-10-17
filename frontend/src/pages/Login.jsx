import React, { useState, useContext } from "react";
import AuthContext from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const { login } = useContext(AuthContext);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data || "Login failed");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      <input value={form.email} onChange={e => setForm({...form, email: e.target.value})} placeholder="Email" required />
      <input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} placeholder="Password" required />
      <button type="submit">Login</button>
      {error && <div style={{color:"red"}}>{JSON.stringify(error)}</div>}
    </form>
  );
}
