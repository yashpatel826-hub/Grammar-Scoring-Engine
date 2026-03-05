import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  signup: (name: string, email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
  isAuthenticated: boolean;
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

  useEffect(() => {
    // Check if user is logged in on mount
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const signup = async (name: string, email: string, password: string) => {
    try {
      // Mock signup logic - store user in localStorage
      const users = JSON.parse(localStorage.getItem("users") || "[]");
      
      // Check if user already exists
      if (users.find((u: any) => u.email === email)) {
        return { success: false, message: "Email already registered" };
      }

      // Add new user
      const newUser = { name, email, password };
      users.push(newUser);
      localStorage.setItem("users", JSON.stringify(users));

      return { success: true };
    } catch (error) {
      return { success: false, message: "Signup failed. Please try again." };
    }
  };

  const login = async (email: string, password: string) => {
    try {
      // Mock login logic - check against localStorage
      const users = JSON.parse(localStorage.getItem("users") || "[]");
      const foundUser = users.find(
        (u: any) => u.email === email && u.password === password
      );

      if (!foundUser) {
        return { success: false, message: "Invalid email or password" };
      }

      const userData = { name: foundUser.name, email: foundUser.email };
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
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
