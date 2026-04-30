import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import RoleRoute from "../RoleRoute";
import AuthContext from "../../contexts/AuthContext";

function renderRoleRoute(user, allowedRoles = ["admin"]) {
  return render(
    <AuthContext.Provider value={{ user }}>
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route element={<RoleRoute allowedRoles={allowedRoles} />}>
            <Route path="/admin" element={<div>Admin Page</div>} />
          </Route>
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("RoleRoute", () => {
  beforeEach(() => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the child route when the user has an allowed role", () => {
    renderRoleRoute({ email: "admin@test.com", role: "admin" });

    expect(screen.getByText("Admin Page")).toBeInTheDocument();
    expect(window.alert).not.toHaveBeenCalled();
  });

  it("redirects disallowed users to the dashboard and alerts them", () => {
    renderRoleRoute({ email: "student@test.com", role: "student" });

    expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    expect(window.alert).toHaveBeenCalledWith("You do not have permission to view this page.");
  });
});
