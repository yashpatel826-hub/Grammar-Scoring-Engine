import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  name: string;
  email: string;
  phone?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  signup: (name: string, email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

  const normalizeEmail = (email: string) => email.trim().toLowerCase();
  useEffect(() => {
    // Check if user is logged in on mount
    try {
      const storedUser = localStorage.getItem("user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    } catch {
      localStorage.removeItem("user");
      setUser(null);
    } finally {
      setIsAuthLoading(false);
    }
  }, []);

  const signup = async (name: string, email: string, password: string) => {
    try {
      const normalizedEmail = normalizeEmail(email);
      const normalizedName = name.trim();

      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: normalizedName,
          email: normalizedEmail,
          password,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        return {
          success: false,
          message: payload?.detail || "Signup failed. Please try again.",
        };
      }

      return { success: true };
    } catch (error) {
      return { success: false, message: "Signup failed. Please try again." };
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const normalizedEmail = normalizeEmail(email);

      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload?.user) {
        return {
          success: false,
          message: payload?.detail || "Invalid email or password",
        };
      }

      const userData = { name: payload.user.name, email: payload.user.email };
      setUser(userData);
      localStorage.setItem("user", JSON.stringify(userData));
      return { success: true };
    } catch (error) {
      return { success: false, message: "Login failed. Please try again." };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
        isAuthLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
