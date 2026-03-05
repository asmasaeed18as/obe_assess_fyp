import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from "recharts";
import api from "../api/axios";
import "../styles/AssessmentCreate.css";
import "../styles/AssessmentGrading.css";

const AssessmentAnalytics = () => {
  const { courseId: paramCourseId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cloChart, setCloChart] = useState([]);
  const [totals, setTotals] = useState({ total_obtained: 0, total_possible: 0 });
  const [coursesList, setCoursesList] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");

  const palette = [
    "#A78BFA",
    "#5db3e4",
    "#4ADE80",
    "#2DD4BF",
    "#F472B6",
    "#FB923C",
  ];

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const [coursesRes, dashRes] = await Promise.all([
          api.get("/courses/"),
          api.get("/users/dashboard-data/"),
        ]);

        const allCourses = Array.isArray(coursesRes.data) ? coursesRes.data : [];
        const dashCourses = Array.isArray(dashRes.data?.courses) ? dashRes.data.courses : [];

        const byId = new Map();
        allCourses.forEach((c) => {
          if (!c?.id) return;
          byId.set(String(c.id), { id: c.id, code: c.code, title: c.title });
        });

        dashCourses.forEach((c) => {
          const id = c.course_id || c.id;
          if (!id) return;
          const existing = byId.get(String(id)) || { id };
          byId.set(String(id), {
            id,
            code: c.code || existing.code,
            title: c.title || existing.title,
            section_name: c.section_name || existing.section_name,
          });
        });

        const merged = Array.from(byId.values());
        setCoursesList(merged);

        const lastCourseId = localStorage.getItem("grading_course_id");
        if (paramCourseId && merged.some((c) => String(c.id) === String(paramCourseId))) {
          setSelectedCourseId(String(paramCourseId));
        } else if (lastCourseId && merged.some((c) => String(c.id) === String(lastCourseId))) {
          setSelectedCourseId(String(lastCourseId));
        } else {
          setSelectedCourseId("__all__");
        }
      } catch (err) {
        try {
          const res = await api.get("/courses/");
          setCoursesList(Array.isArray(res.data) ? res.data : []);
        } catch {
          setCoursesList([]);
        }
        setSelectedCourseId(paramCourseId ? String(paramCourseId) : "__all__");
      } finally {
        setLoading(false);
      }
    };

    loadCourses();
  }, [paramCourseId]);

  useEffect(() => {
    const loadAnalytics = async () => {
      if (!selectedCourseId) return;
      try {
        setLoading(true);
        const res = selectedCourseId === "__all__"
          ? await api.get("/analytics/all/clo/")
          : await api.get(`/courses/${selectedCourseId}/analytics/clo/`);
        const data = res?.data || {};
        const chart = Array.isArray(data.clo_chart) ? data.clo_chart : [];
        setCloChart(chart);
        setTotals({
          total_obtained: data.total_obtained || 0,
          total_possible: data.total_possible || 0,
        });
        setError("");
      } catch (err) {
        console.error("Failed to load analytics:", err);
        setError("Failed to load CLO analytics. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, [selectedCourseId]);

  if (loading && coursesList.length === 0) {
    return (
      <div className="assessment-container" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh" }}>
        <div className="card-section settings-glass-card" style={{ textAlign: "center", maxWidth: "500px" }}>
          <div className="avatar-circle-large" style={{ margin: "0 auto 20px", background: "rgba(var(--primary-rgb), 0.1)" }}>
            Loading
          </div>
          <h2 className="profile-name-display" style={{ fontSize: "1.5rem", marginBottom: "10px" }}>
            Loading Courses...
          </h2>
        </div>
      </div>
    );
  }

  const cloData = cloChart.map((c, idx) => ({
    name: c.clo,
    attainment: c.percent,
    obtained: c.obtained,
    possible: c.possible,
    color: palette[idx % palette.length],
  }));

  const handleExportPdf = () => {
    window.print();
  };

  return (
    <div className="assessment-container" style={{ padding: "20px 40px", height: "100vh", overflow: "hidden", justifyContent: "flex-start" }}>
      <header className="page-header" style={{ marginBottom: "20px" }}>
        <h1 className="page-title">Outcome-Based Analytics</h1>
        <p className="page-subtitle">Visualizing CLO attainment and student performance metrics.</p>
      </header>

      <div className="assessment-form" style={{ maxWidth: "1000px", height: "calc(100% - 120px)", background: "transparent", padding: "0", display: "flex", flexDirection: "column", gap: "20px" }}>
        <div className="card-section">
          <label className="section-label">Select Course</label>
          <select
            className="input-field"
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
          >
            <option value="__all__">All Courses</option>
            {coursesList.map((course) => (
              <option key={course.id} value={course.id}>
                {course.code} - {course.title}{course.section_name ? ` (${course.section_name})` : ""}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="card-section">
            <p className="error-msg">{error}</p>
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", flex: 1, minHeight: "320px" }}>
          <div className="card-section question-card-glass" style={{ flex: 1, display: "flex", flexDirection: "column", padding: "20px" }}>
            <label className="section-label" style={{ marginBottom: "15px" }}>CLO Attainment (%)</label>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={cloData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#000000', fontSize: 14 }} interval={0} />
                <YAxis unit="%" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fill: 'var(--text-main)', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 10px 20px rgba(0,0,0,0.1)" }}
                  cursor={{ fill: "rgba(var(--primary-rgb), 0.05)" }}
                />
                <Bar dataKey="attainment" radius={[10, 10, 0, 0]} barSize={40}>
                  {cloData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card-section question-card-glass" style={{ flex: 1, display: "flex", flexDirection: "column", padding: "20px" }}>
            <label className="section-label" style={{ marginBottom: "15px" }}>Obtained vs Possible Marks</label>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={cloData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#000000', fontSize: 14 }} interval={0} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-main)', fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 10px 20px rgba(0,0,0,0.1)" }} />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: "10px" }} />
                <Bar name="Obtained" dataKey="obtained" fill="#7B61FF" radius={[6, 6, 0, 0]} barSize={25} />
                <Bar name="Possible" dataKey="possible" fill="#f965b9" radius={[6, 6, 0, 0]} barSize={25} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="action-bar-centered" style={{ marginTop: "24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div className="score-summary-badge" style={{ margin: 0 }}>
            Cumulative Score: {totals.total_obtained} / {totals.total_possible}
          </div>
          <button className="generate-btn" style={{ width: "280px" }} type="button" onClick={handleExportPdf}>
            Export PDF Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssessmentAnalytics;
