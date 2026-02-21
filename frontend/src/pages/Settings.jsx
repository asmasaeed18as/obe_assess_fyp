import React, { useState } from "react";
import "../styles/AssessmentCreate.css"; 

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
    <div className="assessment-container" style={{ minHeight: '100vh', paddingBottom: '50px' }}>
      
      {/* Centered Heading - Matches AssessmentCreate.css exactly */}
      <h1 className="page-title">Settings</h1>

      <div className="assessment-form" style={{ maxWidth: '650px', background: '#fff', padding: '30px', borderRadius: '16px' }}>
        
        {/* Profile Header */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '15px', marginBottom: '40px' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#F2F4F7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px' }}>
            👤
          </div>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '600', color: '#101828' }}>{profile.name}</h2>
            <p style={{ margin: 0, color: '#667085' }}>{profile.email}</p>
          </div>
        </div>

        {/* Settings List */}
        <div style={{ borderTop: '1px solid #EAECF0' }}>
          <SettingRow label="Name" value={profile.name} onEdit={(v) => handleChange('name', v)} />
          <SettingRow label="Email account" value={profile.email} onEdit={(v) => handleChange('email', v)} />
          <SettingRow label="Mobile number" value={profile.mobile} onEdit={(v) => handleChange('mobile', v)} />
          <SettingRow label="Location" value={profile.location} onEdit={(v) => handleChange('location', v)} />
          <SettingRow label="Role" value={profile.role} isStatic={true} />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '20px 10px', borderBottom: '1px solid #EAECF0' }}>
             <span style={{ color: '#344054', fontWeight: '500' }}>Courses</span>
             <button style={{ background: 'none', border: 'none', fontWeight: 'bold', cursor: 'pointer', fontSize: '1rem', color: '#000' }}>Edit</button>
          </div>
        </div>

        {/* Save Button */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '40px' }}>
          <button className="settings-pill-btn">
            Save Changes
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