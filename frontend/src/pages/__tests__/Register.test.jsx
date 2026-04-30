import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import Register from "../Register";
import AuthContext from "../../contexts/AuthContext";

function renderRegister(registerMock) {
  return render(
    <AuthContext.Provider value={{ register: registerMock }}>
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("Register page", () => {
  beforeEach(() => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits the form and navigates to login on success", async () => {
    const user = userEvent.setup();
    const registerMock = vi.fn().mockResolvedValue({});
    renderRegister(registerMock);

    await user.type(screen.getByPlaceholderText("Email Address"), "new@test.com");
    await user.type(screen.getByPlaceholderText("Username"), "newuser");
    await user.selectOptions(screen.getByRole("combobox"), "instructor");
    await user.type(screen.getByPlaceholderText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith({
        email: "new@test.com",
        username: "newuser",
        password: "secret123",
        role: "instructor",
      });
    });
    expect(window.alert).toHaveBeenCalledWith("Registered successfully. Please login.");
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  it("shows a fallback error message when registration fails", async () => {
    const user = userEvent.setup();
    const registerMock = vi.fn().mockRejectedValue({
      response: { data: { email: ["Already exists"] } },
    });
    renderRegister(registerMock);

    await user.type(screen.getByPlaceholderText("Email Address"), "new@test.com");
    await user.type(screen.getByPlaceholderText("Username"), "newuser");
    await user.selectOptions(screen.getByRole("combobox"), "student");
    await user.type(screen.getByPlaceholderText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    expect(await screen.findByText("Registration failed")).toBeInTheDocument();
  });
});
