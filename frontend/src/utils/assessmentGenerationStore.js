import api from "../api/axios";

const STORAGE_KEY = "assessmentGenerationState";

let inflightPromise = null;

const defaultState = {
  status: "idle", // idle | in_progress | completed | error
  startedAt: null,
  courseId: null,
  assessmentId: null,
  result: null,
  error: null,
};

const loadState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...defaultState };
    const parsed = JSON.parse(raw);
    return { ...defaultState, ...parsed };
  } catch {
    return { ...defaultState };
  }
};

let state = loadState();
const listeners = new Set();

const persist = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage errors (private mode or quota)
  }
};

const notify = () => {
  listeners.forEach((fn) => fn(state));
};

const setState = (partial) => {
  state = { ...state, ...partial };
  persist();
  notify();
};

export const getAssessmentGenerationState = () => state;

export const subscribeAssessmentGeneration = (fn) => {
  listeners.add(fn);
  fn(state);
  return () => listeners.delete(fn);
};

export const clearAssessmentGeneration = () => {
  inflightPromise = null;
  setState({ ...defaultState });
};

export const hasAssessmentGenerationInFlight = () => Boolean(inflightPromise);

export const startAssessmentGeneration = (formData, courseId) => {
  if (state.status === "in_progress" && inflightPromise) {
    return inflightPromise;
  }

  setState({
    status: "in_progress",
    startedAt: new Date().toISOString(),
    courseId,
    assessmentId: null,
    result: null,
    error: null,
  });

  inflightPromise = api
    .post("/assessment/generate/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((res) => {
      setState({
        status: "completed",
        assessmentId: res.data?.id || null,
        result: res.data || null,
      });
      inflightPromise = null;
      return res;
    })
    .catch((err) => {
      const message =
        err?.response?.data?.error || err?.message || "Failed to generate assessment.";
      setState({ status: "error", error: message });
      inflightPromise = null;
      throw err;
    });

  return inflightPromise;
};
