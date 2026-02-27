import React, { useState } from "react";
import "../styles/AssessmentCreate.css"; 
import "../styles/AssessmentGrading.css"; 

const Settings = () => {
  const [profile, setProfile] = useState({
    name: "your name",
    email: "yourname@gmail.com",
    mobile: "Add number",
    location: "Pakistan",
    role: "Professor"
  });

  const handleChange = (field, value) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="assessment-container" style={{ justifyContent: 'center', padding: '20px 80px' }}>
      <div className="settings-wrapper" style={{ paddingTop: '0' }}>
        <div className="card-section settings-glass-card" style={{ padding: '25px 40px !important' }}>
          
          {/* Compact Profile Header */}
          <div className="profile-header-section" style={{ marginBottom: '20px' }}>
            <div className="avatar-circle-large" style={{ width: '70px', height: '70px', fontSize: '30px' }}>
              👤
            </div>
            <div className="profile-text">
              <h2 className="profile-name-display" style={{ fontSize: '1.4rem' }}>{profile.name}</h2>
              <p className="profile-email-display" style={{ fontSize: '0.9rem' }}>{profile.email}</p>
            </div>
          </div>

          {/* Settings List - Tightened Spacing */}
          <div className="settings-list">
            <SettingRow label="Name" value={profile.name} onEdit={(v) => handleChange('name', v)} />
            <SettingRow label="Email Account" value={profile.email} onEdit={(v) => handleChange('email', v)} />
            <SettingRow label="Mobile Number" value={profile.mobile} onEdit={(v) => handleChange('mobile', v)} />
            <SettingRow label="Location" value={profile.location} onEdit={(v) => handleChange('location', v)} />
            <SettingRow label="Role" value={profile.role} isStatic={true} />
          </div>

          {/* Centered Save Button */}
          <div className="action-bar-centered" style={{ marginTop: '25px' }}>
            <button className="generate-btn" style={{ padding: '12px 24px', width: '220px' }}>
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const SettingRow = ({ label, value, onEdit, isStatic = false }) => (
  <div className="settings-row" style={{ padding: '12px 0' }}>
    <span className="settings-label-text" style={{ fontSize: '0.85rem' }}>{label}</span>
    {isStatic ? (
      /* Now using the same class as inputs to ensure identical font size/styling */
      <span className="settings-input-inline" style={{ border: 'none', background: 'transparent', cursor: 'default' }}>
        {value}
      </span>
    ) : (
      <input 
        type="text" 
        value={value} 
        onChange={(e) => onEdit(e.target.value)}
        className="settings-input-inline"
        style={{ fontSize: '0.9rem' }}
      />
    )}
  </div>
);

export default Settings;