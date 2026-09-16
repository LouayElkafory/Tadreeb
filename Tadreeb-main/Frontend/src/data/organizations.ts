import type { Organization } from "../types";

export const organizations: Organization[] = [
  {
    id: "iti",
    name: {
      ar: "معهد تكنولوجيا المعلومات",
      en: "Information Technology Institute",
    },
    shortName: "ITI",
    description: {
      ar: "جهة تدريب تقني تابعة لوزارة الاتصالات، تقدم برامج تدريبية مكثفة في البرمجة والتقنية لتأهيل الخريجين لسوق العمل.",
      en: "A technology training institute affiliated with Egypt's Ministry of Communications, offering intensive software and technology programs for graduates.",
    },
    categories: [
      { ar: "برمجة", en: "Software" },
      { ar: "بيانات", en: "Data" },
      { ar: "تقنية", en: "Technology" },
    ],
    color: "#38BDF8",
  },
  {
    id: "nti",
    name: {
      ar: "المعهد القومي للاتصالات",
      en: "National Telecommunication Institute",
    },
    shortName: "NTI",
    description: {
      ar: "معهد متخصص في التدريب والتأهيل في الاتصالات وتكنولوجيا المعلومات للطلاب والخريجين والعاملين في القطاع.",
      en: "A specialized institute for training and upskilling students, graduates, and professionals in telecommunications and information technology.",
    },
    categories: [
      { ar: "اتصالات", en: "Telecom" },
      { ar: "شبكات", en: "Networks" },
      { ar: "تقنية", en: "Technology" },
    ],
    color: "#0EA5E9",
  },
  {
    id: "depi",
    name: {
      ar: "مبادرة رواد مصر الرقمية",
      en: "Digital Egypt Pioneers Initiative",
    },
    shortName: "DEPI",
    description: {
      ar: "مبادرة حكومية لتأهيل الشباب في المسارات التقنية الأكثر طلبا بالتعاون مع شركات عالمية رائدة.",
      en: "A national initiative that prepares young talent for in-demand digital tracks in partnership with leading global companies.",
    },
    categories: [
      { ar: "تحول رقمي", en: "Digital" },
      { ar: "برمجة", en: "Software" },
      { ar: "ذكاء اصطناعي", en: "AI" },
    ],
    color: "#2563EB",
  },
  {
    id: "mcit",
    name: {
      ar: "وزارة الاتصالات وتكنولوجيا المعلومات",
      en: "Ministry of Communications and Information Technology",
    },
    shortName: "MCIT",
    description: {
      ar: "الجهة الحكومية المسؤولة عن سياسات التحول الرقمي في مصر وتشرف على عدد من مبادرات التدريب التقني.",
      en: "The government body responsible for Egypt's digital transformation policies and several national technology training initiatives.",
    },
    categories: [
      { ar: "سياسات", en: "Policy" },
      { ar: "مبادرات", en: "Initiatives" },
      { ar: "تحول رقمي", en: "Digital" },
    ],
    color: "#1D4ED8",
  },
  {
    id: "itida",
    name: {
      ar: "هيئة تنمية صناعة تكنولوجيا المعلومات",
      en: "Information Technology Industry Development Agency",
    },
    shortName: "ITIDA",
    description: {
      ar: "هيئة مصرية تدعم نمو صناعة تكنولوجيا المعلومات، وتنمية المهارات الرقمية، وربط المواهب بفرص السوق.",
      en: "Egypt's agency for developing the IT industry, strengthening digital talent, and connecting skills with market opportunities.",
    },
    categories: [
      { ar: "صناعة التكنولوجيا", en: "IT Industry" },
      { ar: "مهارات رقمية", en: "Digital Skills" },
      { ar: "ابتكار", en: "Innovation" },
    ],
    color: "#14B8A6",
  },
];
