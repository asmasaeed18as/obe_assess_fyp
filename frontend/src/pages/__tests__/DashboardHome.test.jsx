import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("../../api/axios", () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock("../../components/AdminView", () => ({
  default: () => <div>Admin View Mock</div>,
}));

vi.mock("../../components/InstructorView", () => ({
  default: ({ user, data }) => (
    <div>
      Instructor View Mock
      <span>{user?.first_name}</span>
      <span>{data?.courses?.length ?? 0}</span>
    </div>
  ),
}));

vi.mock("../../components/StudentView", () => ({
  default: ({ user, data }) => (
    <div>
      Student View Mock
      <span>{user?.first_name}</span>
      <span>{data?.courses?.length ?? 0}</span>
    </div>
  ),
}));

import api from "../../api/axios";
import DashboardHome from "../DashboardHome";
import AuthContext from "../../contexts/AuthContext";

function renderDashboardHome(user) {
  return render(
    <AuthContext.Provider value={{ user }}>
      <DashboardHome />
    </AuthContext.Provider>
  );
}

describe("DashboardHome", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("shows a loading state before dashboard data resolves", () => {
    api.get.mockReturnValue(new Promise(() => {}));

    renderDashboardHome({ role: "student", first_name: "Ali" });

    expect(screen.getByText("Loading Dashboard...")).toBeInTheDocument();
  });

  it("renders the student dashboard when the role is student", async () => {
    api.get.mockResolvedValue({
      data: {
        role: "student",
        courses: [{ id: "s1", code: "CS-101" }],
      },
    });

    renderDashboardHome({ role: "student", first_name: "Ali" });

    expect(await screen.findByText("Student View Mock")).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/users/dashboard-data/");
  });

  it("renders the instructor dashboard when the role is instructor", async () => {
    api.get.mockResolvedValue({
      data: {
        role: "instructor",
        courses: [{ id: "i1", code: "CS-201" }],
      },
    });

    renderDashboardHome({ role: "instructor", first_name: "Ayesha" });

    expect(await screen.findByText("Instructor View Mock")).toBeInTheDocument();
  });

  it("renders the admin dashboard for admin users", async () => {
    api.get.mockResolvedValue({
      data: {
        role: "admin",
        courses: [],
      },
    });

    renderDashboardHome({ role: "admin", first_name: "Admin" });

    expect(await screen.findByText("Admin View Mock")).toBeInTheDocument();
  });

  it("falls back to the auth context role when dashboard data has no role", async () => {
    api.get.mockResolvedValue({
      data: {
        courses: [],
      },
    });

    renderDashboardHome({ role: "instructor", first_name: "Ayesha" });

    expect(await screen.findByText("Instructor View Mock")).toBeInTheDocument();
  });

  it("stops loading even when the dashboard request fails", async () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    api.get.mockRejectedValue(new Error("dashboard failed"));

    renderDashboardHome({ role: "student", first_name: "Ali" });

    await waitFor(() => {
      expect(screen.getByText("Student View Mock")).toBeInTheDocument();
    });

    errorSpy.mockRestore();
  });
});
