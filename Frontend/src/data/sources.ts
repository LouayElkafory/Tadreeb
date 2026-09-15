import type { Source } from "../types";

export const sources: Source[] = [
  {
    id: "src-1",
    title: "دليل القبول في معهد تكنولوجيا المعلومات",
    url: "https://iti.gov.eg/iti/admissions",
    organization: "ITI",
    type: "official",
    description: "الدليل الرسمي لشروط وخطوات التقديم في برامج ITI التدريبية.",
  },
  {
    id: "src-2",
    title: "بوابة وزارة الاتصالات وتكنولوجيا المعلومات",
    url: "https://mcit.gov.eg",
    organization: "MCIT",
    type: "government",
    description: "الموقع الرسمي للوزارة ومبادراتها في التدريب التقني والتحول الرقمي.",
  },
  {
    id: "src-3",
    title: "الدليل التعريفي لمبادرة DEPI",
    url: "https://depi.gov.eg/about",
    organization: "DEPI",
    type: "document",
    description: "مستند تعريفي بمسارات وشركاء مبادرة التدريب الرقمي DEPI.",
  },
  {
    id: "src-4",
    title: "صفحة برامج المعهد القومي للاتصالات",
    url: "https://nti.sci.eg/programs",
    organization: "NTI",
    type: "official",
    description: "قائمة بالبرامج التدريبية المتاحة في المعهد القومي للاتصالات وتكنولوجيا المعلومات.",
  },
  {
    id: "src-5",
    title: "تجارب خريجين في مجتمع تدريب",
    url: "https://community.example.com/graduates",
    organization: "مجتمع تدريب",
    type: "community",
    description: "نقاشات ومشاركات من خريجين سابقين حول تجاربهم في برامج التدريب التقني.",
  },
  {
    id: "src-6",
    title: "الأسئلة الشائعة حول القبول في NTI",
    url: "https://nti.sci.eg/faq",
    organization: "NTI",
    type: "official",
    description: "إجابات على أكثر الأسئلة شيوعًا حول شروط ومواعيد التقديم.",
  },
];
