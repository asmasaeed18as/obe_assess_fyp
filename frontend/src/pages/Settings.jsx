import React, { useState, useEffect, useContext } from "react";
import api from "../api/axios";
import AuthContext from "../contexts/AuthContext";
import "../styles/AssessmentCreate.css"; 

const Settings = () => {
  const { user } = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    role: ""
  });

  const displayName = [profile.first_name, profile.last_name].filter(Boolean).join(" ")
    || profile.username
    || (user?.first_name ? user.first_name : "")
    || "Your Name";

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const res = await api.get("/users/me/");
        const data = res?.data || {};
        setProfile({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          username: data.username || "",
          email: data.email || "",
          role: data.role || ""
        });
      } catch (err) {
        console.error("Failed to load profile:", err);
        setError("Failed to load profile.");
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleChange = (field, value) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const res = await api.put("/users/me/", {
        first_name: profile.first_name,
        last_name: profile.last_name,
        username: profile.username,
        email: profile.email
      });
      const data = res?.data || {};
      setProfile(prev => ({
        ...prev,
        first_name: data.first_name || prev.first_name,
        last_name: data.last_name || prev.last_name,
        username: data.username || prev.username,
        email: data.email || prev.email,
        role: data.role || prev.role
      }));
    } catch (err) {
      console.error("Failed to save profile:", err);
      setError("Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="assessment-container">
        <h1 className="page-title">Settings</h1>
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="assessment-container" style={{ minHeight: '100vh', paddingBottom: '50px' }}>
      <h1 className="page-title">Settings</h1>

      <div className="assessment-form" style={{ maxWidth: '650px', background: '#fff', padding: '30px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '15px', marginBottom: '40px' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#F2F4F7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px' }}>
            
          </div>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '600', color: '#101828' }}>{displayName}</h2>
            <p style={{ margin: 0, color: '#667085' }}>{profile.email || ""}</p>
          </div>
        </div>

        {error && <p className="error-msg">{error}</p>}

        <div style={{ borderTop: '1px solid #EAECF0' }}>
          <SettingRow label="First Name" value={profile.first_name} onEdit={(v) => handleChange('first_name', v)} />
          <SettingRow label="Last Name" value={profile.last_name} onEdit={(v) => handleChange('last_name', v)} />
          <SettingRow label="Username" value={profile.username} onEdit={(v) => handleChange('username', v)} />
          <SettingRow label="Email" value={profile.email} onEdit={(v) => handleChange('email', v)} />
          <SettingRow label="Role" value={profile.role} isStatic={true} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '40px' }}>
          <button className="settings-pill-btn" onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
};

const SettingRow = ({ label, value, onEdit, isStatic = false }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 10px', borderBottom: '1px solid #EAECF0' }}>
    <span style={{ color: '#667085', fontSize: '1rem' }}>{label}</span>
    {isStatic ? (
      <span style={{ color: '#101828', fontWeight: '500' }}>{value}</span>
    ) : (
      <input 
        type="text" 
        value={value} 
        onChange={(e) => onEdit(e.target.value)}
        className="clean-inline-input"
      />
    )}
  </div>
);

export default Settings;
