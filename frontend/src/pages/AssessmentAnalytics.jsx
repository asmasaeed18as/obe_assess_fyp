import React, { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import api from "../api/axios";
import "../styles/AssessmentCreate.css"; 
import "../styles/AssessmentGrading.css"; 

const AssessmentAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cloChart, setCloChart] = useState([]);
  const [totals, setTotals] = useState({ total_obtained: 0, total_possible: 0 });

  const palette = ['#FF9F59', '#7B61FF', '#1e7d20', '#2AA7A1', '#C05621', '#4C51BF'];

  useEffect(() => {
    const loadAnalytics = async () => {
      const submissionId = localStorage.getItem("grading_submission_id");
      if (!submissionId) {
        setError("No graded submission found. Please grade an assessment first.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const res = await api.get(`/analytics/submission/${submissionId}/clo/`);
        const data = res?.data || {};
        const chart = Array.isArray(data.clo_chart) ? data.clo_chart : [];
        setCloChart(chart);
        setTotals({
          total_obtained: data.total_obtained || 0,
          total_possible: data.total_possible || 0
        });
      } catch (err) {
        console.error("Failed to load analytics:", err);
        setError("Failed to load CLO analytics. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  // Styled Loading/Error State
  if (loading || error) {
    return (
      <div className="assessment-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <div className="card-section settings-glass-card" style={{ textAlign: 'center', maxWidth: '500px' }}>
          <div className="avatar-circle-large" style={{ margin: '0 auto 20px', background: 'rgba(99, 102, 241, 0.1)' }}>
            {loading ? "📊" : "⚠️"}
          </div>
          <h2 className="profile-name-display" style={{ fontSize: '1.5rem', marginBottom: '10px' }}>
            {loading ? "Generating Analytics..." : "Notice"}
          </h2>
          <p className="profile-email-display" style={{ fontSize: '1rem', lineHeight: '1.5' }}>
            {error || "We are crunching the numbers for your Outcome-Based evaluation."}
          </p>
          {error && (
             <button 
              className="generate-btn" 
              style={{ marginTop: '20px', width: 'auto', padding: '10px 30px' }}
              onClick={() => window.location.href='grading'}
            >
              Go to Grading
            </button>
          )}
        </div>
      </div>
    );
  }

  const cloData = cloChart.map((c, idx) => ({
    name: c.clo,
    attainment: c.percent,
    obtained: c.obtained,
    possible: c.possible,
    color: palette[idx % palette.length]
  }));

  return (
    <div className="assessment-container" style={{ padding: '20px 40px', height: '100vh', overflow: 'hidden', justifyContent: 'flex-start' }}>
      <header className="page-header" style={{ marginBottom: '20px' }}>
        <h1 className="page-title">Outcome-Based Analytics</h1>
        <p className="page-subtitle">Visualizing CLO attainment and student performance metrics.</p>
      </header>

      <div className="assessment-form" style={{ maxWidth: '1000px', height: 'calc(100% - 120px)', background: 'transparent', padding: '0', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', flex: 1, minHeight: '0' }}>
          {/* Chart 1 */}
          <div className="card-section question-card-glass" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '20px' }}>
            <label className="section-label" style={{ marginBottom: '15px' }}>CLO Attainment (%)</label>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cloData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis unit="%" domain={[0, 100]} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 20px rgba(0,0,0,0.1)' }}
                  cursor={{fill: 'rgba(99, 102, 241, 0.05)'}} 
                />
                <Bar dataKey="attainment" radius={[10, 10, 0, 0]} barSize={40}>
                  {cloData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 2 */}
          <div className="card-section question-card-glass" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '20px' }}>
            <label className="section-label" style={{ marginBottom: '15px' }}>Obtained vs Possible Marks</label>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cloData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 20px rgba(0,0,0,0.1)' }} />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '10px' }} />
                <Bar name="Obtained" dataKey="obtained" fill="#7B61FF" radius={[6, 6, 0, 0]} barSize={25} />
                <Bar name="Possible" dataKey="possible" fill="#E2E8F0" radius={[6, 6, 0, 0]} barSize={25} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="action-bar-centered" style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="score-summary-badge" style={{ margin: 0 }}>
            Cumulative Score: {totals.total_obtained} / {totals.total_possible}
          </div>
          <button className="generate-btn" style={{ width: '280px' }}>
            Export PDF Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssessmentAnalytics;
