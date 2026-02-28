import React, { useState, useEffect } from "react";
import AuthContext from "./AuthContext";
import api from "../api/axios";
import { jwtDecode } from "jwt-decode";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user on refresh
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        setUser(jwtDecode(token));
      } catch (e) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setUser(null);
      }
    }
    setLoading(false);
  }, []);

  // LOGIN
  const login = async (email, password) => {
    const res = await api.post("/users/login/", { email, password });
    const { access, refresh } = res.data;

    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);

    setUser(jwtDecode(access));
    return res.data;
  };

  // REGISTER
  const register = (data) => api.post("/users/register/", data);

  // UPDATE PROFILE
  const updateProfile = async (data) => {
    const res = await api.put("/users/me/", data);
    return res.data;
  };

  // LOGOUT
  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}
