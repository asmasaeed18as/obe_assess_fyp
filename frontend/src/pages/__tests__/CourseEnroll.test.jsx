import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

vi.mock("../../api/axios", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import api from "../../api/axios";
import CourseEnroll from "../CourseEnroll";

const hierarchyPayload = [
  {
    id: 1,
    name: "SEECS",
    programs: [
      {
        id: 10,
        name: "BSCS",
        batches: [
          {
            id: 100,
            name: "BSCS-13",
            semesters: [
              {
                id: 1000,
                name: "Spring 2026",
                sections: [
                  {
                    id: "section-1",
                    course_code: "CS-305",
                    course_title: "Software Testing",
                    section_name: "A",
                    instructor_name: "teacher@test.com",
                  },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
];

function renderCourseEnroll() {
  return render(
    <MemoryRouter initialEntries={["/dashboard/enroll-course"]}>
      <Routes>
        <Route path="/dashboard/enroll-course" element={<CourseEnroll />} />
        <Route path="/dashboard" element={<div>Dashboard Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("CourseEnroll", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows a loading state while hierarchy is being fetched", () => {
    api.get.mockReturnValue(new Promise(() => {}));

    renderCourseEnroll();

    expect(screen.getByText("Loading course catalog...")).toBeInTheDocument();
  });

  it("renders hierarchy filters and course cards after loading", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: hierarchyPayload });

    renderCourseEnroll();

    await screen.findByText("Enroll in a Class");
    await user.selectOptions(screen.getByRole("combobox", { name: /Department/i }), "1");
    await user.selectOptions(screen.getByRole("combobox", { name: /Program/i }), "10");
    await user.click(screen.getByRole("button", { name: "BSCS-13" }));

    expect(screen.getByText("Software Testing")).toBeInTheDocument();
    expect(screen.getByText(/Semester Spring 2026/i)).toBeInTheDocument();
  });

  it("alerts when trying to join without an enrollment code", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: hierarchyPayload });

    renderCourseEnroll();

    await screen.findByText("Enroll in a Class");
    await user.selectOptions(screen.getByRole("combobox", { name: /Department/i }), "1");
    await user.selectOptions(screen.getByRole("combobox", { name: /Program/i }), "10");
    await user.click(screen.getByRole("button", { name: "BSCS-13" }));
    await user.click(screen.getByRole("button", { name: "Join" }));

    expect(window.alert).toHaveBeenCalledWith("Please enter the Enrollment Code provided by your instructor.");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("submits the enrollment code and navigates to dashboard on success", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: hierarchyPayload });
    api.post.mockResolvedValue({
      data: {
        message: "Successfully joined CS-305 (A)",
      },
    });

    renderCourseEnroll();

    await screen.findByText("Enroll in a Class");
    await user.selectOptions(screen.getByRole("combobox", { name: /Department/i }), "1");
    await user.selectOptions(screen.getByRole("combobox", { name: /Program/i }), "10");
    await user.click(screen.getByRole("button", { name: "BSCS-13" }));
    await user.type(screen.getByPlaceholderText("Enroll Code"), "abc123");
    await user.click(screen.getByRole("button", { name: "Join" }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/join/", { enrollment_code: "ABC123" });
    });
    expect(window.alert).toHaveBeenCalledWith("✅ Success: Successfully joined CS-305 (A)");
    expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
  });

  it("shows the backend error message when joining fails", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: hierarchyPayload });
    api.post.mockRejectedValue({
      response: {
        data: {
          error: "Invalid code",
        },
      },
    });

    renderCourseEnroll();

    await screen.findByText("Enroll in a Class");
    await user.selectOptions(screen.getByRole("combobox", { name: /Department/i }), "1");
    await user.selectOptions(screen.getByRole("combobox", { name: /Program/i }), "10");
    await user.click(screen.getByRole("button", { name: "BSCS-13" }));
    await user.type(screen.getByPlaceholderText("Enroll Code"), "BAD999");
    await user.click(screen.getByRole("button", { name: "Join" }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith("❌ Invalid code");
    });
  });
});
