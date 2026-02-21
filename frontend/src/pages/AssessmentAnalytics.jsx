import React, { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import "../styles/AssessmentCreate.css"; 

const AssessmentAnalytics = () => {
  const [loading, setLoading] = useState(true);

  const cloData = [
    { name: 'CLO-1', attainment: 38, color: '#FF9F59' }, 
    { name: 'CLO-2', attainment: 22, color: '#7B61FF' }, 
    { name: 'CLO-3', attainment: 65, color: '#1e7d20' }, 
  ];

  const distributionData = [
    { range: '0-20', count: 5 },
    { range: '21-40', count: 15 },
    { range: '41-60', count: 25 },
    { range: '61-80', count: 18 },
    { range: '81-100', count: 7 },
  ];

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  if (loading) return <div className="assessment-container"><h1>Loading Analytics...</h1></div>;

  return (
    <div className="assessment-container" style={{ padding: '10px 20px', height: '100vh', overflow: 'hidden', justifyContent: 'flex-start' }}>
      
      <h1 className="page-title" style={{ marginBottom: '10px', fontSize: '1.5rem' }}>Outcome-Based Analytics</h1>

      {/* Container for Charts and Button */}
      <div className="assessment-form" style={{ maxWidth: '900px', height: 'calc(100% - 60px)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        
        {/* Top Chart */}
        <div className="card-section card-purple" style={{ flex: 1, minHeight: '0', padding: '12px' }}>
          <label className="section-label">CLO Attainment (%)</label>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={cloData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ccc" />
              <XAxis dataKey="name" />
              <YAxis unit="%" domain={[0, 100]} />
              <Tooltip cursor={{fill: 'rgba(255,255,255,0.5)'}} />
              <Bar dataKey="attainment" radius={[6, 6, 0, 0]} barSize={50}>
                {cloData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Bottom Chart */}
        <div className="card-section card-green" style={{ flex: 1, minHeight: '0', padding: '12px' }}>
          <label className="section-label">Student Performance Distribution</label>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="range" />
              <YAxis label={{ value: 'Students', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="count" fill="#1e7d20" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Export Button at the very bottom */}
        <button className="generate-btn" style={{ marginTop: '5px', padding: '12px', fontSize: '1rem' }}>
          Export Analytics Report (PDF)
        </button>

      </div>
    </div>
  );
};

export default AssessmentAnalytics;