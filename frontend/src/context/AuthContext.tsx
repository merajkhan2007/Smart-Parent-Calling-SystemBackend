import React, { createContext, useContext, useState, useEffect } from "react";

interface User {
  email: string;
  name: string;
  role: "Super Admin" | "School Admin" | "Teacher";
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe: boolean) => Promise<void>;
  logout: () => void;
  apiFetch: (url: string, options?: RequestInit) => Promise<any>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage or sessionStorage
  useEffect(() => {
    const savedToken = localStorage.getItem("spcs_token") || sessionStorage.getItem("spcs_token");
    const savedUser = localStorage.getItem("spcs_user") || sessionStorage.getItem("spcs_user");

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string, rememberMe: boolean) => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/login-json", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, remember_me: rememberMe }),
      });

      if (!response.ok) {
        let errorMsg = "Authentication failed";
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch (e) {
          errorMsg = `Server error (${response.status}): Make sure the backend server is running at http://localhost:8000.`;
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const userPayload: User = {
        email: data.email,
        name: data.name,
        role: data.role,
      };

      setToken(data.access_token);
      setUser(userPayload);

      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem("spcs_token", data.access_token);
      storage.setItem("spcs_refresh", data.refresh_token);
      storage.setItem("spcs_user", JSON.stringify(userPayload));
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("spcs_token");
    localStorage.removeItem("spcs_refresh");
    localStorage.removeItem("spcs_user");
    sessionStorage.removeItem("spcs_token");
    sessionStorage.removeItem("spcs_refresh");
    sessionStorage.removeItem("spcs_user");
  };

  // Wrapper for authenticated API requests that attaches headers and handles refreshments
  const apiFetch = async (url: string, options: RequestInit = {}): Promise<any> => {
    let currentToken = token || localStorage.getItem("spcs_token") || sessionStorage.getItem("spcs_token");

    const headers = {
      ...options.headers,
      "Authorization": `Bearer ${currentToken}`,
    };

    let response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      // Access token expired, attempt to refresh
      const rToken = localStorage.getItem("spcs_refresh") || sessionStorage.getItem("spcs_refresh");
      if (rToken) {
        try {
          const refreshRes = await fetch(`/api/auth/refresh?refresh_token=${rToken}`, {
            method: "POST",
          });
          if (refreshRes.ok) {
            const data = await refreshRes.json();
            setToken(data.access_token);
            const rememberMe = !!localStorage.getItem("spcs_refresh");
            const storage = rememberMe ? localStorage : sessionStorage;
            storage.setItem("spcs_token", data.access_token);
            storage.setItem("spcs_refresh", data.refresh_token);

            // Retry request
            headers["Authorization"] = `Bearer ${data.access_token}`;
            response = await fetch(url, { ...options, headers });
          } else {
            logout();
            throw new Error("Session expired. Please log in again.");
          }
        } catch (e) {
          logout();
          throw new Error("Session expired. Please log in again.");
        }
      } else {
        logout();
        throw new Error("Session expired. Please log in again.");
      }
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "An error occurred" }));
      throw new Error(err.detail || "Request failed");
    }

    // Return JSON if present, else text
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    }
    return response;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        apiFetch,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
