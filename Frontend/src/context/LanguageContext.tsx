import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Language } from '@/types'

interface Dictionary {
  [key: string]: { ar: string; en: string }
}

const dictionary: Dictionary = {
  nav_home: { ar: 'الرئيسية', en: 'Home' },
  nav_sources: { ar: 'المصادر', en: 'Sources' },
  nav_assistant: { ar: 'المساعد الذكي', en: 'AI Assistant' },
  nav_institutions: { ar: 'المؤسسات', en: 'Institutions' },
  nav_programs: { ar: 'البرامج', en: 'Programs' },
  nav_login: { ar: 'دخول', en: 'Log in' },
  hero_headline: { ar: 'اسأل عن التدريب. وإحنا نجيبلك الإجابة.', en: 'Ask about training. We\u2019ll bring you the answer.' },
  hero_subheadline: { ar: 'مساعدك الذكي لاكتشاف فرص التدريب التقني.', en: 'Your smart guide to discovering technical training opportunities.' },
  hero_support: {
    ar: 'مساعد ذكي بيساعدك تعرف البرامج، شروط التقديم، التخصصات، ومدة التدريب من مصادر موثوقة.',
    en: 'A smart assistant that helps you learn about programs, admission requirements, tracks, and duration — from trusted sources.',
  },
  hero_cta_primary: { ar: 'ابدأ المحادثة', en: 'Start chatting' },
  hero_cta_secondary: { ar: 'اكتشف البرامج', en: 'Explore programs' },
  hero_trust: { ar: 'إجابات مبنية على مصادر موثوقة', en: 'Answers grounded in trusted sources' },
  hero_input_placeholder: { ar: 'اسأل أي حاجة عن ITI، NTI، DEPI...', en: 'Ask anything about ITI, NTI, DEPI...' },
  chat_title: { ar: 'مساعد تدريب', en: 'Tadreeb Assistant' },
  chat_status: { ar: 'متصل', en: 'Online' },
  chat_trust_label: { ar: 'بيجاوبك من مصادر موثوقة', en: 'Answers from trusted sources' },
  chat_new: { ar: 'محادثة جديدة', en: 'New chat' },
}

interface LanguageContextValue {
  lang: Language
  dir: 'rtl' | 'ltr'
  toggleLang: () => void
  setLang: (lang: Language) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => {
    const stored = localStorage.getItem('tadreeb.lang')
    return stored === 'en' ? 'en' : 'ar'
  })

  const dir: 'rtl' | 'ltr' = lang === 'ar' ? 'rtl' : 'ltr'

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = dir
    localStorage.setItem('tadreeb.lang', lang)
  }, [lang, dir])

  const setLang = (next: Language) => setLangState(next)
  const toggleLang = () => setLangState((prev) => (prev === 'ar' ? 'en' : 'ar'))

  const t = (key: string) => dictionary[key]?.[lang] ?? key

  const value = useMemo(
    () => ({ lang, dir, toggleLang, setLang, t }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lang, dir],
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
