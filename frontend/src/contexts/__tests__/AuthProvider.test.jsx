import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

vi.mock("../../api/axios", () => ({
  default: {
    post: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("jwt-decode", () => ({
  jwtDecode: vi.fn(),
}));

import api from "../../api/axios";
import { jwtDecode } from "jwt-decode";
import { AuthProvider } from "../AuthProvider";
import AuthContext from "../AuthContext";

function AuthConsumer() {
  const { user, loading, login, logout } = React.useContext(AuthContext);

  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user-email">{user?.email ?? "none"}</div>
      <button onClick={() => login("teacher@test.com", "secret123")}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("loads the user from a stored access token", async () => {
    localStorage.setItem("access_token", "saved-access");
    jwtDecode.mockReturnValue({ email: "teacher@test.com", role: "instructor" });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("teacher@test.com");
  });

  it("clears invalid stored tokens", async () => {
    localStorage.setItem("access_token", "bad-access");
    localStorage.setItem("refresh_token", "bad-refresh");
    jwtDecode.mockImplementation(() => {
      throw new Error("invalid token");
    });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(screen.getByTestId("user-email")).toHaveTextContent("none");
  });

  it("logs in, stores tokens, and updates the user", async () => {
    const user = userEvent.setup();
    api.post.mockResolvedValue({
      data: {
        access: "new-access",
        refresh: "new-refresh",
      },
    });
    jwtDecode.mockReturnValue({ email: "teacher@test.com", role: "instructor" });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await user.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/users/login/", {
        email: "teacher@test.com",
        password: "secret123",
      });
    });
    expect(localStorage.getItem("access_token")).toBe("new-access");
    expect(localStorage.getItem("refresh_token")).toBe("new-refresh");
    expect(screen.getByTestId("user-email")).toHaveTextContent("teacher@test.com");
  });

  it("logs out and removes stored tokens", async () => {
    const user = userEvent.setup();
    localStorage.setItem("access_token", "saved-access");
    localStorage.setItem("refresh_token", "saved-refresh");
    jwtDecode.mockReturnValue({ email: "teacher@test.com", role: "instructor" });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("teacher@test.com");
    });

    await user.click(screen.getByRole("button", { name: "Logout" }));

    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(screen.getByTestId("user-email")).toHaveTextContent("none");
  });
});
