import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import DashboardLayout from "../Dashboard";
import AuthContext from "../../contexts/AuthContext";

function renderDashboardLayout(user, logout = vi.fn(), initialEntry = "/dashboard") {
  return render(
    <AuthContext.Provider value={{ user, logout }}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<div>Home Content</div>} />
            <Route path="admin" element={<div>Admin Content</div>} />
            <Route path="settings" element={<div>Settings Content</div>} />
            <Route path="create-assessment" element={<div>Create Assessment Content</div>} />
            <Route path="analytics" element={<div>Analytics Content</div>} />
            <Route path="grading" element={<div>Grading Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("DashboardLayout", () => {
  it("shows a loading screen when there is no user yet", () => {
    renderDashboardLayout(null);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders instructor-specific navigation links", () => {
    renderDashboardLayout({
      role: "instructor",
      email: "teacher@test.com",
      first_name: "Ayesha",
    });

    expect(screen.getByRole("link", { name: /Assessments/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Analytics/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Grading/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Admin Console/i })).not.toBeInTheDocument();
  });

  it("renders the admin console link for admin users", () => {
    renderDashboardLayout({
      role: "admin",
      email: "admin@test.com",
      first_name: "Root",
    });

    expect(screen.getByRole("link", { name: /Admin Console/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Assessments/i })).not.toBeInTheDocument();
  });

  it("logs out and navigates to login", async () => {
    const user = userEvent.setup();
    const logout = vi.fn();
    renderDashboardLayout(
      {
        role: "student",
        email: "student@test.com",
        first_name: "Ali",
      },
      logout
    );

    await user.click(screen.getByRole("button", { name: /Logout/i }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });
});
