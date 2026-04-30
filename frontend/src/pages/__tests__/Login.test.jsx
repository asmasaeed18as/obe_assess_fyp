import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import Login from "../Login";
import AuthContext from "../../contexts/AuthContext";

function renderLogin(loginMock) {
  return render(
    <AuthContext.Provider value={{ login: loginMock }}>
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("Login page", () => {
  it("submits credentials and navigates to the dashboard on success", async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockResolvedValue({});
    renderLogin(loginMock);

    await user.type(screen.getByLabelText("Email Address"), "teacher@test.com");
    await user.type(screen.getByLabelText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("teacher@test.com", "secret123");
    });
    expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
  });

  it("shows the API error message when login fails", async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockRejectedValue({
      response: { data: { detail: "Invalid credentials" } },
    });
    renderLogin(loginMock);

    await user.type(screen.getByLabelText("Email Address"), "teacher@test.com");
    await user.type(screen.getByLabelText("Password"), "wrongpass");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
  });
});
