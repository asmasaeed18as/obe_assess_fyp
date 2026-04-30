import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import InstructorView from "../InstructorView";

function renderInstructorView(props) {
  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <Routes>
        <Route path="/dashboard" element={<InstructorView {...props} />} />
        <Route path="/dashboard/courses/:id" element={<div>Course Detail Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("InstructorView", () => {
  it("shows an empty state when the instructor has no courses", () => {
    renderInstructorView({
      user: { first_name: "Ayesha" },
      data: { courses: [] },
    });

    expect(screen.getByText(/No assigned courses found/i)).toBeInTheDocument();
  });

  it("navigates to course detail when a course card is clicked", async () => {
    const user = userEvent.setup();
    renderInstructorView({
      user: { first_name: "Ayesha" },
      data: {
        courses: [{ course_id: 12, title: "Software Testing", code: "CS-305", section_name: "Section A" }],
      },
    });

    await user.click(screen.getByText("Software Testing"));

    expect(screen.getByText("Course Detail Page")).toBeInTheDocument();
  });
});
