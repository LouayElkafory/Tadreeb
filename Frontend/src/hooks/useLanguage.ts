import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { createElement } from "react";

export type Language = "ar" | "en";

interface LanguageContextValue {
  language: Language;
  toggleLanguage: () => void;
  dir: "rtl" | "ltr";
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const stored = window.localStorage.getItem("tadreeb-lang");
    return stored === "en" ? "en" : "ar";
  });

  const dir = language === "ar" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = dir;
    window.localStorage.setItem("tadreeb-lang", language);
  }, [language, dir]);

  const toggleLanguage = () => setLanguage((prev) => (prev === "ar" ? "en" : "ar"));

  return createElement(
    LanguageContext.Provider,
    { value: { language, toggleLanguage, dir } },
    children
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
