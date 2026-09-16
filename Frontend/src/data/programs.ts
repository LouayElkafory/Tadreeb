import type { Program, Track } from "../types";

export const tracks: Track[] = [
  {
    id: "ai",
    name: { ar: "الذكاء الاصطناعي", en: "Artificial Intelligence" },
    description: {
      ar: "تعلم الآلة، معالجة اللغة، والتطبيقات الذكية.",
      en: "Machine learning, language processing, and intelligent applications.",
    },
  },
  {
    id: "data",
    name: { ar: "علوم البيانات", en: "Data Science" },
    description: {
      ar: "تحليل البيانات، الإحصاء، والتصور البصري.",
      en: "Data analysis, statistics, and visualization.",
    },
  },
  {
    id: "cyber",
    name: { ar: "الأمن السيبراني", en: "Cybersecurity" },
    description: {
      ar: "حماية الأنظمة والشبكات من التهديدات الرقمية.",
      en: "Protecting systems and networks from digital threats.",
    },
  },
  {
    id: "web",
    name: { ar: "تطوير الويب", en: "Web Development" },
    description: {
      ar: "بناء تطبيقات الويب الحديثة من الواجهة إلى الخلفية.",
      en: "Building modern web applications from frontend to backend.",
    },
  },
  {
    id: "cloud",
    name: { ar: "الحوسبة السحابية", en: "Cloud Computing" },
    description: {
      ar: "إدارة ونشر الأنظمة على المنصات السحابية.",
      en: "Managing and deploying systems on cloud platforms.",
    },
  },
  {
    id: "network",
    name: { ar: "الشبكات", en: "Networks" },
    description: {
      ar: "تصميم وإدارة الشبكات والبنية التحتية التقنية.",
      en: "Designing and managing networks and technical infrastructure.",
    },
  },
];

export const programs: Program[] = [
  {
    id: "iti-ai-pro",
    name: {
      ar: "برنامج الذكاء الاصطناعي المتقدم",
      en: "Advanced Artificial Intelligence Program",
    },
    organization: "iti",
    track: "ai",
    level: "advanced",
    description: {
      ar: "برنامج مكثف يغطي تعلم الآلة والتعلم العميق وتطبيقات الذكاء الاصطناعي العملية.",
      en: "An intensive program covering machine learning, deep learning, and practical AI applications.",
    },
    skills: ["Python", "Machine Learning", "Deep Learning", "NLP"],
  },
  {
    id: "iti-web-fullstack",
    name: {
      ar: "تطوير الويب المتكامل",
      en: "Full-Stack Web Development",
    },
    organization: "iti",
    track: "web",
    level: "intermediate",
    description: {
      ar: "مسار شامل لتعلم تطوير الواجهات الأمامية والخلفية وبناء تطبيقات ويب متكاملة.",
      en: "A complete track for frontend, backend, and full-stack web application development.",
    },
    skills: ["JavaScript", "React", "Node.js", "Databases"],
  },
  {
    id: "nti-network-eng",
    name: {
      ar: "هندسة الشبكات",
      en: "Network Engineering",
    },
    organization: "nti",
    track: "network",
    level: "intermediate",
    description: {
      ar: "تأهيل فني ومهني في تصميم وإدارة الشبكات والبنية التحتية للاتصالات.",
      en: "Technical and professional preparation in network design, administration, and telecom infrastructure.",
    },
    skills: ["Networking", "Cisco", "Infrastructure"],
  },
  {
    id: "nti-cyber-fundamentals",
    name: {
      ar: "أساسيات الأمن السيبراني",
      en: "Cybersecurity Fundamentals",
    },
    organization: "nti",
    track: "cyber",
    level: "beginner",
    description: {
      ar: "مقدمة في مفاهيم الأمن السيبراني وحماية الأنظمة من الهجمات الشائعة.",
      en: "An introduction to cybersecurity concepts and protecting systems against common attacks.",
    },
    skills: ["Security Basics", "Risk Assessment"],
  },
  {
    id: "depi-data-science",
    name: {
      ar: "مسار علوم البيانات",
      en: "Data Science Track",
    },
    organization: "depi",
    track: "data",
    level: "intermediate",
    description: {
      ar: "برنامج تدريبي بالتعاون مع شركات عالمية لتأهيل محللي ومهندسي بيانات.",
      en: "A training program delivered with global partners to prepare data analysts and engineers.",
    },
    skills: ["Python", "SQL", "Data Visualization"],
  },
  {
    id: "depi-cloud-devops",
    name: {
      ar: "الحوسبة السحابية و DevOps",
      en: "Cloud Computing and DevOps",
    },
    organization: "depi",
    track: "cloud",
    level: "advanced",
    description: {
      ar: "مسار متقدم لتعلم نشر وإدارة الأنظمة السحابية وممارسات DevOps الحديثة.",
      en: "An advanced track for cloud deployment, operations, and modern DevOps practices.",
    },
    skills: ["AWS", "Docker", "CI/CD"],
  },
  {
    id: "mcit-digital-foundations",
    name: {
      ar: "أساسيات التحول الرقمي",
      en: "Digital Transformation Foundations",
    },
    organization: "mcit",
    track: "web",
    level: "beginner",
    description: {
      ar: "برنامج تمهيدي لفهم أساسيات العمل في المجالات التقنية والتحول الرقمي.",
      en: "A foundation program for understanding technical careers and digital transformation basics.",
    },
    skills: ["Digital Literacy", "Problem Solving"],
  },
  {
    id: "itida-freelance-ready",
    name: {
      ar: "الجاهزية للعمل الحر الرقمي",
      en: "Digital Freelancing Readiness",
    },
    organization: "itida",
    track: "web",
    level: "beginner",
    description: {
      ar: "مسار يساعد المتدربين على تجهيز ملفهم المهني وفهم متطلبات سوق العمل الرقمي والعمل الحر.",
      en: "A track that helps learners prepare their professional profile and understand digital work and freelancing requirements.",
    },
    skills: ["Portfolio", "Communication", "Market Readiness"],
  },
  {
    id: "iti-cyber-advanced",
    name: {
      ar: "الأمن السيبراني المتقدم",
      en: "Advanced Cybersecurity",
    },
    organization: "iti",
    track: "cyber",
    level: "advanced",
    description: {
      ar: "تدريب متعمق في اختبار الاختراق والاستجابة للحوادث الأمنية.",
      en: "Advanced training in penetration testing and security incident response.",
    },
    skills: ["Penetration Testing", "Incident Response"],
  },
];
