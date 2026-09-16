import type { Source } from "../types";

export const sources: Source[] = [
  {
    id: "src-1",
    title: {
      ar: "دليل القبول في معهد تكنولوجيا المعلومات",
      en: "Information Technology Institute Admissions Guide",
    },
    url: "https://iti.gov.eg/iti/admissions",
    organization: { ar: "ITI", en: "ITI" },
    type: "official",
    description: {
      ar: "الدليل الرسمي لشروط وخطوات التقديم في برامج ITI التدريبية.",
      en: "The official guide for admission requirements and application steps for ITI training programs.",
    },
  },
  {
    id: "src-2",
    title: {
      ar: "بوابة وزارة الاتصالات وتكنولوجيا المعلومات",
      en: "Ministry of Communications and Information Technology Portal",
    },
    url: "https://mcit.gov.eg",
    organization: { ar: "MCIT", en: "MCIT" },
    type: "government",
    description: {
      ar: "الموقع الرسمي للوزارة ومبادراتها في التدريب التقني والتحول الرقمي.",
      en: "The ministry's official site and its initiatives for technology training and digital transformation.",
    },
  },
  {
    id: "src-3",
    title: {
      ar: "الدليل التعريفي لمبادرة DEPI",
      en: "DEPI Initiative Overview",
    },
    url: "https://depi.gov.eg/about",
    organization: { ar: "DEPI", en: "DEPI" },
    type: "document",
    description: {
      ar: "مستند تعريفي بمسارات وشركاء مبادرة رواد مصر الرقمية.",
      en: "An overview of DEPI tracks, partners, and training pathways.",
    },
  },
  {
    id: "src-4",
    title: {
      ar: "صفحة برامج المعهد القومي للاتصالات",
      en: "National Telecommunication Institute Programs",
    },
    url: "https://nti.sci.eg/programs",
    organization: { ar: "NTI", en: "NTI" },
    type: "official",
    description: {
      ar: "قائمة بالبرامج التدريبية المتاحة في المعهد القومي للاتصالات.",
      en: "A list of training programs available through the National Telecommunication Institute.",
    },
  },
  {
    id: "src-5",
    title: {
      ar: "تجارب خريجين في مجتمع تدريب",
      en: "Graduate Experiences in the Tadreeb Community",
    },
    url: "https://community.example.com/graduates",
    organization: { ar: "مجتمع تدريب", en: "Tadreeb Community" },
    type: "community",
    description: {
      ar: "نقاشات ومشاركات من خريجين سابقين حول تجاربهم في برامج التدريب التقني.",
      en: "Community discussions and graduate stories about technical training programs.",
    },
  },
  {
    id: "src-6",
    title: {
      ar: "الأسئلة الشائعة حول القبول في NTI",
      en: "NTI Admissions FAQ",
    },
    url: "https://nti.sci.eg/faq",
    organization: { ar: "NTI", en: "NTI" },
    type: "official",
    description: {
      ar: "إجابات على أكثر الأسئلة شيوعا حول شروط ومواعيد التقديم.",
      en: "Answers to common questions about admission requirements and application timelines.",
    },
  },
];
