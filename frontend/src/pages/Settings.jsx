import React, { useState, useEffect, useContext } from "react";
import api from "../api/axios";
import AuthContext from "../contexts/AuthContext";
import "../styles/AssessmentCreate.css"; 

const Settings = () => {
  const { user } = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  
  const [profile, setProfile] = useState({
    first_name: "", last_name: "", username: "", email: "", role: ""
  });

  // Password change states
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: ""
  });

  const displayName = [profile.first_name, profile.last_name].filter(Boolean).join(" ")
    || profile.username
    || "User";

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
          // Capitalize first letter of role
          role: data.role ? data.role.charAt(0).toUpperCase() + data.role.slice(1) : ""
        });
      } catch (err) {
        setError("Failed to load profile.");
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, []);

  const handlePasswordChange = (e) => {
    setPasswords({ ...passwords, [e.target.name]: e.target.value });
    setError("");
    setSuccess("");
  };

  const onUpdatePassword = async (e) => {
    e.preventDefault();
    if (passwords.new_password !== passwords.confirm_password) {
      setError("New passwords do not match.");
      return;
    }

    setSaving(true);
    try {
      await api.post("/users/change-password/", {
        old_password: passwords.current_password,
        new_password: passwords.new_password
      });
      setSuccess("Password updated successfully!");
      setPasswords({ current_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update password. Check your current password.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="assessment-container"><div className="settings-wrapper">Loading...</div></div>;

  return (
    <div className="assessment-container">
      <div className="settings-wrapper">
        <div className="card-section settings-glass-card">
          <div className="profile-header-section">
            <div className="avatar-circle-large">
              {profile.first_name ? profile.first_name[0] : (profile.username ? profile.username[0].toUpperCase() : "U")}
            </div>
            <h2 className="profile-name-display">{displayName}</h2>
            <p className="profile-email-display" style={{ fontSize: '0.85rem' }}>{profile.email}</p>
          </div>

          <div className="settings-list">
            <SettingRow label="First Name" value={profile.first_name} isStatic={true} />
            <SettingRow label="Last Name" value={profile.last_name} isStatic={true} />
            <SettingRow label="Username" value={profile.username} isStatic={true} />
            <SettingRow label="Email" value={profile.email} isStatic={true} />
            <SettingRow label="Role" value={profile.role} isStatic={true} />
          </div>

          <div className="password-change-section" style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '15px', color: '#4c1d95' }}>Change Password</h3>
            <div className="settings-list">
              <div className="settings-row" style={{ padding: '8px 0' }}>
                <span className="settings-label-text" style={{ flex: '1' }}>Current Password</span>
                <input 
                  type="password" 
                  name="current_password"
                  value={passwords.current_password}
                  onChange={handlePasswordChange}
                  className="settings-input-inline"
                  style={{ flex: '1.5', background: 'rgba(255,255,255,0.5)' }} 
                />
              </div>
              <div className="settings-row" style={{ padding: '8px 0' }}>
                <span className="settings-label-text" style={{ flex: '1' }}>New Password</span>
                <input 
                  type="password" 
                  name="new_password"
                  value={passwords.new_password}
                  onChange={handlePasswordChange}
                  className="settings-input-inline"
                  style={{ flex: '1.5', background: 'rgba(255,255,255,0.5)' }} 
                />
              </div>
              <div className="settings-row" style={{ padding: '8px 0' }}>
                <span className="settings-label-text" style={{ flex: '1' }}>Confirm Password</span>
                <input 
                  type="password" 
                  name="confirm_password"
                  value={passwords.confirm_password}
                  onChange={handlePasswordChange}
                  className="settings-input-inline"
                  style={{ flex: '1.5', background: 'rgba(255,255,255,0.5)' }} 
                />
              </div>
            </div>

            <button 
              className="generate-btn" 
              style={{ width: '100%', marginTop: '20px' }} 
              onClick={onUpdatePassword} 
              disabled={saving || !passwords.new_password}
            >
              {saving ? "Updating..." : "Update Password"}
            </button>
            
            {error && <p className="error-msg" style={{ marginTop: '10px', color: '#ff4d4f', textAlign: 'center' }}>{error}</p>}
            {success && <p className="success-msg" style={{ marginTop: '10px', color: '#52c41a', textAlign: 'center' }}>{success}</p>}
          </div>
        </div>
      </div>
    </div>
  );
};

const SettingRow = ({ label, value, isStatic = false }) => (
  <div className="settings-row" style={{ padding: '12px 0', display: 'flex', alignItems: 'center' }}>
    <span className="settings-label-text" style={{ flex: '1' }}>{label}</span>
    <span className="settings-value-static" style={{ flex: '2', textAlign: 'right', fontWeight: '500', color: '#666' }}>
      {value || "N/A"}
    </span>
  </div>
);

export default Settings;