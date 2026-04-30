import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import ProtectedRoute from "../ProtectedRoute";
import AuthContext from "../../contexts/AuthContext";

function renderProtectedRoute(contextValue) {
  return render(
    <AuthContext.Provider value={contextValue}>
      <MemoryRouter initialEntries={["/private"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/private" element={<div>Private Page</div>} />
          </Route>
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("ProtectedRoute", () => {
  it("renders nothing while auth is loading", () => {
    const { container } = renderProtectedRoute({ user: null, loading: true });

    expect(container).toBeEmptyDOMElement();
  });

  it("redirects unauthenticated users to login", () => {
    renderProtectedRoute({ user: null, loading: false });

    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  it("renders the child route for authenticated users", () => {
    renderProtectedRoute({
      user: { email: "teacher@test.com", role: "instructor" },
      loading: false,
    });

    expect(screen.getByText("Private Page")).toBeInTheDocument();
  });
});
