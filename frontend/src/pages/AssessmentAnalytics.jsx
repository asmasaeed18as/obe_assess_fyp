import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import api from "../api/axios";
import "../styles/AssessmentCreate.css";
import "../styles/AssessmentGrading.css";
import ThemedSelect from "../components/ThemedSelect";

const PALETTE = ["#A78BFA", "#5db3e4", "#4ADE80", "#2DD4BF", "#F472B6", "#FB923C"];
const TYPE_COLORS = {
  Quiz: "#A78BFA",
  Assignment: "#5db3e4",
  Exam: "#4ADE80",
  Lab: "#F472B6",
  Project: "#FB923C",
};
const DIST_COLORS = {
  "0-50": "#ef4444",
  "50-60": "#f97316",
  "60-70": "#eab308",
  "70-80": "#84cc16",
  "80-90": "#22c55e",
  "90-100": "#10b981",
};
const DIST_KEYS = ["0-50", "50-60", "60-70", "70-80", "80-90", "90-100"];

const EmptyChart = ({ height = 220, message = "No data yet" }) => (
  <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted, #888)", fontSize: "0.9rem" }}>
    {message}
  </div>
);

const ChartCard = ({ title, children }) => (
  <div className="card-section question-card-glass" style={{ padding: "20px", display: "flex", flexDirection: "column" }}>
    <label className="section-label" style={{ marginBottom: "14px" }}>{title}</label>
    {children}
  </div>
);

const AssessmentAnalytics = () => {
  const { courseId: paramCourseId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cloChart, setCloChart] = useState([]);
  const [cloAttainment, setCloAttainment] = useState({});
  const [historicalTrend, setHistoricalTrend] = useState([]);
  const [assessmentTypeStats, setAssessmentTypeStats] = useState({});
  const [totals, setTotals] = useState({ total_obtained: 0, total_possible: 0 });
  const [coursesList, setCoursesList] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");

  const courseOptions = [
    { value: "__all__", label: "All Courses" },
    ...coursesList.map((c) => ({
      value: String(c.id),
      label: `${c.code} - ${c.title}${c.section_name ? ` (${c.section_name})` : ""}`,
    })),
  ];

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const [coursesRes, dashRes] = await Promise.all([
          api.get("/courses/"),
          api.get("/users/dashboard-data/"),
        ]);
        const allCourses = Array.isArray(coursesRes.data) ? coursesRes.data : (coursesRes.data?.results || []);
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
          byId.set(String(id), { id, code: c.code || existing.code, title: c.title || existing.title, section_name: c.section_name || existing.section_name });
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
      } catch {
        setCoursesList([]);
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
        setCloChart(Array.isArray(data.clo_chart) ? data.clo_chart : []);
        setCloAttainment(data.clo_attainment && typeof data.clo_attainment === "object" ? data.clo_attainment : {});
        setHistoricalTrend(Array.isArray(data.historical_trend) ? data.historical_trend : []);
        setAssessmentTypeStats(data.assessment_type_stats && typeof data.assessment_type_stats === "object" ? data.assessment_type_stats : {});
        setTotals({ total_obtained: data.total_obtained || 0, total_possible: data.total_possible || 0 });
        setError("");
      } catch (err) {
        console.error("Failed to load analytics:", err);
        setError("Failed to load analytics. Please try again.");
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
          <h2 className="profile-name-display" style={{ fontSize: "1.5rem", marginBottom: "10px" }}>Loading Courses...</h2>
        </div>
      </div>
    );
  }

  // Radar: one point per CLO
  const radarData = cloChart.map((c) => ({ subject: c.clo, attainment: c.percent, fullMark: 100 }));

  // Score distribution: one group per CLO, stacked by score bucket
  const distributionData = Object.entries(cloAttainment).map(([clo, stats]) => ({
    name: clo,
    ...(stats.distribution || {}),
  }));

  // Assessment type comparison: one group per CLO, bar per type
  const typeKeys = Object.keys(assessmentTypeStats);
  const allTypeClos = [...new Set(typeKeys.flatMap((t) => Object.keys(assessmentTypeStats[t])))].sort();
  const typeCompData = allTypeClos.map((clo) => {
    const entry = { clo };
    typeKeys.forEach((t) => { entry[t] = assessmentTypeStats[t][clo] ?? 0; });
    return entry;
  });

  const tooltipStyle = { borderRadius: "12px", border: "none", boxShadow: "0 10px 20px rgba(0,0,0,0.1)" };
  const axisStyle = { fill: "var(--text-main)", fontSize: 12 };

  return (
    <div className="assessment-container" style={{ padding: "20px 40px", overflowY: "auto", minHeight: "100vh" }}>
      <header className="page-header" style={{ marginBottom: "20px" }}>
        <h1 className="page-title">Outcome-Based Analytics</h1>
        <p className="page-subtitle">Visualizing CLO attainment and student performance metrics.</p>
      </header>

      <div style={{ maxWidth: "1200px", display: "flex", flexDirection: "column", gap: "20px" }}>
        <div className="card-section">
          <label className="section-label">Select Course</label>
          <ThemedSelect
            className="input-field themed-field field-lg"
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            options={courseOptions}
            placeholder="Select Course"
          />
        </div>

        {error && <div className="card-section"><p className="error-msg">{error}</p></div>}

        {/* Row 1: Historical Trend + Score Distribution */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          <ChartCard title="Historical Trend">
            {historicalTrend.length === 0 ? <EmptyChart message="No trend data yet — submit some graded work first" /> : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={historicalTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={axisStyle} />
                  <YAxis unit="%" domain={[0, 100]} axisLine={false} tickLine={false} tick={axisStyle} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`, "Avg Attainment"]} />
                  <Line type="monotone" dataKey="avg_attainment" stroke="#A78BFA" strokeWidth={3} dot={{ r: 5, fill: "#A78BFA" }} activeDot={{ r: 7 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard title="Score Distribution">
            {distributionData.length === 0 ? <EmptyChart message="No distribution data yet" /> : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={distributionData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={axisStyle} />
                  <YAxis axisLine={false} tickLine={false} tick={axisStyle} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: "8px", fontSize: "11px" }} />
                  {DIST_KEYS.map((key) => (
                    <Bar key={key} dataKey={key} name={key} stackId="dist" fill={DIST_COLORS[key]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>

        {/* Row 2: Radar + Assessment Type Comparison */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          <ChartCard title="CLO Strengths & Weaknesses">
            {radarData.length === 0 ? <EmptyChart message="No CLO data yet" /> : (
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(0,0,0,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={axisStyle} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ ...axisStyle, fontSize: 10 }} />
                  <Radar name="Attainment" dataKey="attainment" stroke="#A78BFA" fill="#A78BFA" fillOpacity={0.4} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`, "Attainment"]} />
                  <Legend iconType="circle" />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard title="Assessment Type Comparison">
            {typeCompData.length === 0 ? <EmptyChart message="No type data yet — title submissions with 'Quiz', 'Exam', etc." /> : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={typeCompData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                  <XAxis dataKey="clo" axisLine={false} tickLine={false} tick={axisStyle} />
                  <YAxis unit="%" domain={[0, 100]} axisLine={false} tickLine={false} tick={axisStyle} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`]} />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: "8px" }} />
                  {typeKeys.map((t, i) => (
                    <Bar key={t} dataKey={t} name={t} fill={TYPE_COLORS[t] || PALETTE[i % PALETTE.length]} radius={[4, 4, 0, 0]} barSize={20} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>

        {/* Summary bar */}
        <div className="action-bar-centered" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "30px" }}>
          <div className="score-summary-badge" style={{ margin: 0 }}>
            Cumulative Score: {totals.total_obtained} / {totals.total_possible}
          </div>
          <button className="generate-btn" style={{ width: "280px" }} type="button" onClick={() => window.print()}>
            Export PDF Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssessmentAnalytics;
