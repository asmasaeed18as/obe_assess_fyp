import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/axios", () => ({
  default: {
    post: vi.fn(),
  },
}));

import api from "../../api/axios";

const loadStoreModule = async () => import("../assessmentGenerationStore");

describe("assessmentGenerationStore", () => {
  beforeEach(async () => {
    localStorage.clear();
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("starts in idle state by default", async () => {
    const store = await loadStoreModule();

    expect(store.getAssessmentGenerationState().status).toBe("idle");
    expect(store.hasAssessmentGenerationInFlight()).toBe(false);
  });

  it("ignores persisted completed state on reload", async () => {
    localStorage.setItem(
      "assessmentGenerationState",
      JSON.stringify({ status: "completed", result: { id: "a1" } })
    );

    const store = await loadStoreModule();

    expect(store.getAssessmentGenerationState().status).toBe("idle");
    expect(store.getAssessmentGenerationState().result).toBeNull();
  });

  it("notifies subscribers about successful generation", async () => {
    const store = await loadStoreModule();
    const listener = vi.fn();
    const formData = new FormData();
    formData.append("course_id", "12");
    api.post.mockResolvedValue({ data: { id: "assessment-1", result_json: { questions: [] } } });

    const unsubscribe = store.subscribeAssessmentGeneration(listener);
    await store.startAssessmentGeneration(formData, "12");

    expect(listener).toHaveBeenCalled();
    expect(store.getAssessmentGenerationState().status).toBe("completed");
    expect(store.getAssessmentGenerationState().assessmentId).toBe("assessment-1");
    expect(store.hasAssessmentGenerationInFlight()).toBe(false);
    unsubscribe();
  });

  it("stores an error message when generation fails", async () => {
    const store = await loadStoreModule();
    const formData = new FormData();
    api.post.mockRejectedValue({
      response: { data: { error: "LLM unavailable" } },
    });

    await expect(store.startAssessmentGeneration(formData, "7")).rejects.toBeTruthy();

    expect(store.getAssessmentGenerationState().status).toBe("error");
    expect(store.getAssessmentGenerationState().error).toBe("LLM unavailable");
  });

  it("clears state explicitly", async () => {
    const store = await loadStoreModule();
    api.post.mockResolvedValue({ data: { id: "assessment-1" } });
    await store.startAssessmentGeneration(new FormData(), "3");

    store.clearAssessmentGeneration();

    expect(store.getAssessmentGenerationState().status).toBe("idle");
    expect(store.getAssessmentGenerationState().assessmentId).toBeNull();
  });
});
