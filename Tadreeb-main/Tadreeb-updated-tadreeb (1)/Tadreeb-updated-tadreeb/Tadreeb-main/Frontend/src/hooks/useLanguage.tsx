import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Language } from "../types";

const dictionary = {
  ar: {
    navHome: "الرئيسية",
    navSources: "المصادر",
    navChat: "المساعد الذكي",
    navInstitutions: "المؤسسات",
    navPrograms: "البرامج",
    login: "دخول",
    langSwitch: "English",
    heroTitle: "اسأل عن التدريب. وإحنا نجيبلك الإجابة.",
    heroSubtitle: "مساعدك الذكي لاكتشاف فرص التدريب التقني.",
    heroBody:
      "مساعد ذكي بيساعدك تعرف البرامج، شروط التقديم، التخصصات، ومدة التدريب من مصادر موثوقة.",
    ctaPrimary: "ابدأ المحادثة",
    ctaSecondary: "اكتشف البرامج",
    trustBadge: "إجابات مبنية على مصادر موثوقة",
    chatPlaceholder: "اسأل أي حاجة عن ITI، NTI، DEPI...",
    footerRights: "جميع الحقوق محفوظة",
  },
  en: {
    navHome: "Home",
    navSources: "Sources",
    navChat: "AI Assistant",
    navInstitutions: "Institutions",
    navPrograms: "Programs",
    login: "Sign in",
    langSwitch: "العربية",
    heroTitle: "Ask about training. We'll bring you the answer.",
    heroSubtitle: "Your AI guide to technical training opportunities.",
    heroBody:
      "A smart assistant that helps you learn about programs, admission requirements, tracks, and duration from trusted sources.",
    ctaPrimary: "Start the conversation",
    ctaSecondary: "Explore programs",
    trustBadge: "Answers grounded in trusted sources",
    chatPlaceholder: "Ask anything about ITI, NTI, DEPI...",
    footerRights: "All rights reserved",
  },
} as const;

type DictKey = keyof typeof dictionary.ar;

interface LanguageContextValue {
  lang: Language;
  dir: "rtl" | "ltr";
  toggleLang: () => void;
  t: (key: DictKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>("ar");
  const dir = lang === "ar" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.setAttribute("lang", lang);
    document.documentElement.setAttribute("dir", dir);
  }, [lang, dir]);

  const toggleLang = () => setLang((prev) => (prev === "ar" ? "en" : "ar"));
  const t = (key: DictKey) => dictionary[lang][key];

  return (
    <LanguageContext.Provider value={{ lang, dir, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
