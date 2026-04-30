import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import Navbar from "../Navbar";
import AuthContext from "../../contexts/AuthContext";

function renderNavbar(contextValue, initialEntries = ["/dashboard"]) {
  return render(
    <AuthContext.Provider value={contextValue}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route
            path="*"
            element={
              <>
                <Navbar />
                <div>Current Page</div>
              </>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("Navbar", () => {
  it("shows the login link when no user is present", () => {
    renderNavbar({ user: null, logout: vi.fn() }, ["/"]);

    expect(screen.getByRole("link", { name: "Login" })).toBeInTheDocument();
  });

  it("shows the logged in username", () => {
    renderNavbar({
      user: { username: "ayesha", role: "instructor" },
      logout: vi.fn(),
    });

    expect(screen.getByText("ayesha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
  });

  it("logs out and navigates to login", async () => {
    const user = userEvent.setup();
    const logout = vi.fn();
    renderNavbar({
      user: { username: "ayesha", role: "instructor" },
      logout,
    });

    await user.click(screen.getByRole("button", { name: "Logout" }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });
});
