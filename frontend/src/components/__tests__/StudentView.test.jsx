import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import StudentView from "../StudentView";

function renderStudentView(props) {
  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <Routes>
        <Route path="/dashboard" element={<StudentView {...props} />} />
        <Route path="/dashboard/enroll-course" element={<div>Enroll Page</div>} />
        <Route path="/dashboard/courses/:id" element={<div>Course Detail Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("StudentView", () => {
  it("shows an empty state when the student has no courses", () => {
    renderStudentView({
      user: { first_name: "Ali" },
      data: { courses: [] },
    });

    expect(screen.getByText("No active courses found.")).toBeInTheDocument();
  });

  it("navigates to enroll page from the hero action", async () => {
    const user = userEvent.setup();
    renderStudentView({
      user: { first_name: "Ali" },
      data: { courses: [] },
    });

    await user.click(screen.getByRole("button", { name: /Enroll in New Course/i }));

    expect(screen.getByText("Enroll Page")).toBeInTheDocument();
  });

  it("navigates to course detail when a course card is clicked", async () => {
    const user = userEvent.setup();
    renderStudentView({
      user: { first_name: "Ali" },
      data: {
        courses: [{ id: "sec-1", title: "Software Testing", code: "CS-305", section_name: "A" }],
      },
    });

    await user.click(screen.getByText("Software Testing"));

    expect(screen.getByText("Course Detail Page")).toBeInTheDocument();
  });
});
