import React, { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import api from "../api/axios";
import "../styles/AssessmentCreate.css"; 

const AssessmentAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cloChart, setCloChart] = useState([]);
  const [totals, setTotals] = useState({ total_obtained: 0, total_possible: 0 });

  const palette = ['#FF9F59', '#7B61FF', '#1e7d20', '#2AA7A1', '#C05621', '#4C51BF'];

  useEffect(() => {
    const loadAnalytics = async () => {
      const storedIds = localStorage.getItem("grading_submission_ids");
      let submissionId = localStorage.getItem("grading_submission_id");
      if (storedIds) {
        try {
          const ids = JSON.parse(storedIds);
          if (Array.isArray(ids) && ids.length > 0) {
            submissionId = ids[ids.length - 1];
          }
        } catch (e) {
          // ignore parse error and fallback to single id
        }
      }
      if (!submissionId) {
        setError("No graded submission found. Please grade an assessment first.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const res = storedIds
          ? await api.post(`/analytics/submissions/clo/`, { submission_ids: JSON.parse(storedIds) })
          : await api.get(`/analytics/submission/${submissionId}/clo/`);
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

  if (loading) return <div className="assessment-container"><h1>Loading Analytics...</h1></div>;
  if (error) return <div className="assessment-container"><h1>{error}</h1></div>;

  const cloData = cloChart.map((c, idx) => ({
    name: c.clo,
    attainment: c.percent,
    obtained: c.obtained,
    possible: c.possible,
    color: palette[idx % palette.length]
  }));

  return (
    <div className="assessment-container" style={{ padding: '10px 20px', height: '100vh', overflow: 'hidden', justifyContent: 'flex-start' }}>
      <h1 className="page-title" style={{ marginBottom: '10px', fontSize: '1.5rem' }}>Outcome-Based Analytics</h1>

      <div className="assessment-form" style={{ maxWidth: '900px', height: 'calc(100% - 60px)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
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

        <div className="card-section card-green" style={{ flex: 1, minHeight: '0', padding: '12px' }}>
          <label className="section-label">CLO Marks (Obtained vs Possible)</label>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={cloData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Marks', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="obtained" fill="#1e7d20" radius={[4, 4, 0, 0]} barSize={28} />
              <Bar dataKey="possible" fill="#7B61FF" radius={[4, 4, 0, 0]} barSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="score-summary-badge" style={{ alignSelf: 'flex-end' }}>
          Total: {totals.total_obtained} / {totals.total_possible}
        </div>

        <button className="generate-btn" style={{ marginTop: '5px', padding: '12px', fontSize: '1rem' }}>
          Export Analytics Report (PDF)
        </button>
      </div>
    </div>
  );
};

export default AssessmentAnalytics;

