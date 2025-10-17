import React, { useContext, useState } from "react";
import AuthContext from "../contexts/AuthContext";
import "../styles/Profile.css";

export default function Profile() {
  const { user, updateProfile, logout } = useContext(AuthContext);
  const [form, setForm] = useState({ username: user?.username || "", first_name: user?.first_name || "", last_name: user?.last_name || "" });
  const [msg, setMsg] = useState("");

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      await updateProfile(form);
      setMsg("Saved!");
    // eslint-disable-next-line no-unused-vars
    } catch (err) {
      setMsg("Failed to save");
    }
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div>
      <h2>Profile</h2>
      <div>Email: {user.email}</div>
      <div>Role: {user.role}</div>
      <form onSubmit={handleSave}>
        <input value={form.username} onChange={e => setForm({...form, username:e.target.value})} placeholder="Username" />
        <input value={form.first_name} onChange={e => setForm({...form, first_name:e.target.value})} placeholder="First name" />
        <input value={form.last_name} onChange={e => setForm({...form, last_name:e.target.value})} placeholder="Last name" />
        <button type="submit">Save</button>
      </form>
      <button onClick={logout}>Logout</button>
      {msg && <div>{msg}</div>}
    </div>
  );
}
