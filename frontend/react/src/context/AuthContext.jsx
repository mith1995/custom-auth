import { createContext, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext(null);
const USER_KEY = "flowspace_demo_user";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); }
    catch { return null; }
  });

  useEffect(() => {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  }, [user]);

  const value = useMemo(() => ({
    user,
    signIn: (email, password) => {
      // Demo-only authentication. Replace this with your backend API call.
      const saved = JSON.parse(localStorage.getItem(USER_KEY) || "null");
      if (saved && saved.email.toLowerCase() === email.toLowerCase()) {
        setUser(saved);
      } else {
        const demoUser = { name: email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, c => c.toUpperCase()), email };
        setUser(demoUser);
      }
      return true;
    },
    register: (name, email) => {
      const newUser = { name, email };
      setUser(newUser);
      return true;
    },
    signOut: () => setUser(null),
  }), [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
