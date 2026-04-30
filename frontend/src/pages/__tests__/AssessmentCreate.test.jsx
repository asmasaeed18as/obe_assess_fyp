import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

vi.mock("../../api/axios", () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock("../../utils/assessmentGenerationStore", () => ({
  subscribeAssessmentGeneration: vi.fn(),
  startAssessmentGeneration: vi.fn(),
  clearAssessmentGeneration: vi.fn(),
  getAssessmentGenerationState: vi.fn(),
  hasAssessmentGenerationInFlight: vi.fn(),
}));

import api from "../../api/axios";
import AssessmentCreate from "../AssessmentCreate";
import {
  clearAssessmentGeneration,
  getAssessmentGenerationState,
  hasAssessmentGenerationInFlight,
  startAssessmentGeneration,
  subscribeAssessmentGeneration,
} from "../../utils/assessmentGenerationStore";

const courseList = [{ id: 12, code: "CS-305", title: "Software Testing" }];
const clos = [
  { code: "CLO-1", bloom_level: "C2" },
  { code: "CLO-2", bloom_level: "C3" },
];

function renderAssessmentCreate(initialRoute = "/dashboard/create-assessment") {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/dashboard/create-assessment" element={<AssessmentCreate />} />
        <Route path="/dashboard/courses/:id/create-assessment" element={<AssessmentCreate />} />
        <Route path="/dashboard/courses/:id" element={<div>Course Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

async function openThemedSelect(labelText, optionText) {
  const label = screen.getByText(labelText);
  const selectRoot = label.parentElement.querySelector(".themed-select-trigger");
  await userEvent.click(selectRoot);
  await userEvent.click(await screen.findByRole("button", { name: optionText }));
}

describe("AssessmentCreate", () => {
  let storeListener;

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    storeListener = null;
    getAssessmentGenerationState.mockReturnValue({
      status: "idle",
      startedAt: null,
      courseId: null,
      assessmentId: null,
      result: null,
      error: null,
    });
    hasAssessmentGenerationInFlight.mockReturnValue(false);
    subscribeAssessmentGeneration.mockImplementation((listener) => {
      storeListener = listener;
      listener(getAssessmentGenerationState());
      return () => {};
    });
    api.get.mockImplementation((url) => {
      if (url === "/courses/") {
        return Promise.resolve({ data: courseList });
      }
      if (url === "/courses/12/clos/") {
        return Promise.resolve({ data: clos });
      }
      if (url === "/courses/12/") {
        return Promise.resolve({ data: { title: "Software Testing" } });
      }
      return Promise.reject(new Error(`Unhandled GET ${url}`));
    });
  });

  it("loads courses, builds question rows, and auto-fills bloom level from selected CLO", async () => {
    const user = userEvent.setup();
    renderAssessmentCreate();

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/courses/");
    });

    await openThemedSelect("Select Course", "CS-305 - Software Testing");
    await openThemedSelect("Assessment Details", "Quiz/MCQs");
    await user.type(screen.getByPlaceholderText("Number of questions"), "2");

    expect(screen.getByText("Q1")).toBeInTheDocument();
    expect(screen.getByText("Q2")).toBeInTheDocument();

    const cloButtons = screen.getAllByText("CLO");
    await user.click(cloButtons[0].closest("button"));
    await user.click(await screen.findByRole("button", { name: "CLO-1 (C2)" }));

    const bloomButtons = screen.getAllByText("C2");
    expect(bloomButtons.length).toBeGreaterThan(0);
  });

  it("validates required fields before starting generation", async () => {
    const user = userEvent.setup();
    renderAssessmentCreate();

    await user.click(screen.getByRole("button", { name: "Generate Assessment" }));
    expect(screen.getByText("Please select a course.")).toBeInTheDocument();

    await openThemedSelect("Select Course", "CS-305 - Software Testing");
    await user.click(screen.getByRole("button", { name: "Generate Assessment" }));
    expect(screen.getByText("Please select an assessment type.")).toBeInTheDocument();
  });

  it("submits topic-mode generation with built form data", async () => {
    const user = userEvent.setup();
    startAssessmentGeneration.mockResolvedValue({});
    renderAssessmentCreate();

    await openThemedSelect("Select Course", "CS-305 - Software Testing");
    await openThemedSelect("Assessment Details", "Assignment");
    await user.type(screen.getByPlaceholderText("Number of questions"), "1");

    await user.click(screen.getByRole("button", { name: "Enter Topic" }));
    await user.type(screen.getByPlaceholderText("Enter topic or instructions..."), "Testing strategies");

    const cloButton = screen.getByText("CLO").closest("button");
    await user.click(cloButton);
    await user.click(await screen.findByRole("button", { name: "CLO-1 (C2)" }));

    const marksInput = screen.getByDisplayValue("5");
    await user.clear(marksInput);
    await user.type(marksInput, "10");

    await user.click(screen.getByRole("button", { name: "Generate Assessment" }));

    await waitFor(() => {
      expect(startAssessmentGeneration).toHaveBeenCalledTimes(1);
    });

    const [formData, courseId] = startAssessmentGeneration.mock.calls[0];
    expect(courseId).toBe(12);
    expect(formData.get("course_id")).toBe("12");
    expect(formData.get("assessment_type")).toBe("Assignment");
    expect(formData.get("topic_input")).toBe("Testing strategies");
    expect(JSON.parse(formData.get("questions_config"))[0]).toMatchObject({
      clo: "CLO-1",
      weightage: "10",
    });
  });

  it("renders completed generation state and supports clearing status", async () => {
    const user = userEvent.setup();
    renderAssessmentCreate("/dashboard/courses/12/create-assessment");

    await act(async () => {
      storeListener({
        status: "completed",
        courseId: "12",
        assessmentId: "a1",
        result: {
          id: "a1",
          result_json: {
            questions: [
              {
                id: 1,
                question: "What is unit testing?",
                marks: 5,
                meta: { clo: "CLO-1", bloom: "C2", difficulty: "Easy" },
              },
            ],
          },
        },
        error: null,
      });
    });

    expect(await screen.findByText("Assessment generated successfully.")).toBeInTheDocument();
    expect(screen.getByText("What is unit testing?")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Clear Status" }));
    expect(clearAssessmentGeneration).toHaveBeenCalledTimes(1);
  });

  it("navigates to the course page from completed generation actions", async () => {
    const user = userEvent.setup();
    renderAssessmentCreate("/dashboard/courses/12/create-assessment");

    await act(async () => {
      storeListener({
        status: "completed",
        courseId: "12",
        assessmentId: "a1",
        result: {
          id: "a1",
          result_json: {
            questions: [
              {
                id: 1,
                question: "What is unit testing?",
                marks: 5,
                meta: { clo: "CLO-1", bloom: "C2", difficulty: "Easy" },
              },
            ],
          },
        },
        error: null,
      });
    });

    await user.click(screen.getByRole("button", { name: "View In Course" }));
    expect(screen.getByText("Course Page")).toBeInTheDocument();
  });

  it("shows a persisted in-progress warning after refresh when no request is active", async () => {
    getAssessmentGenerationState.mockReturnValue({
      status: "in_progress",
      startedAt: "2026-04-30T10:00:00.000Z",
      courseId: "12",
      assessmentId: null,
      result: null,
      error: null,
    });
    hasAssessmentGenerationInFlight.mockReturnValue(false);

    renderAssessmentCreate();

    expect(
      await screen.findByText(/A generation request was in progress, but this page was refreshed/i)
    ).toBeInTheDocument();
  });
});
