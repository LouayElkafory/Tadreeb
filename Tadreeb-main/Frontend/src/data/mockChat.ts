import type { ChatApiResponse, Language, LocalizedText } from "../types";
import { sources } from "./sources";

const DEFAULT_SUGGESTIONS: Record<Language, string[]> = {
  ar: [
    "طب إيه الأوراق المطلوبة؟",
    "هل في اختبار قبول؟",
    "مدة التدريب كام؟",
    "إمتى التقديم؟",
  ],
  en: [
    "What documents are required?",
    "Is there an admission test?",
    "How long is the training?",
    "When does application open?",
  ],
};

interface Rule {
  keywords: string[];
  answer: LocalizedText;
  sourceIds: string[];
  suggestions: Record<Language, string[]>;
}

const rules: Rule[] = [
  {
    keywords: ["ازيك", "عامل ايه", "أهلاً", "اهلا", "مرحبا", "صباح الخير", "مساء الخير", "hello", "hi", "hey"],
    answer: {
      ar: "أهلاً بك! أنا **مساعد تدريب الذكي** 👋. أقدر أساعدك تستكشف وتعرف كل تفاصيل برامج التدريب التقني في مصر زي **ITI**، **NTI**، **DEPI**، و**MCIT** (شروط التقديم، المسارات، مدة التدريب، والأوراق المطلوبة). تحب تسأل عن إيه؟",
      en: "Hello! I am **Tadreeb AI Assistant** 👋. I can help you explore technical training opportunities in Egypt like **ITI**, **NTI**, **DEPI**, and **MCIT** (admission requirements, tracks, duration, and documents). What would you like to know?",
    },
    sourceIds: ["src-1", "src-2"],
    suggestions: {
      ar: ["إيه البرامج المناسبة ليا؟", "احكيلي عن برامج NTI", "إيه شروط التقديم في ITI؟", "هل التدريب مجاني؟"],
      en: ["Which programs fit me?", "Tell me about NTI programs", "What are ITI admission requirements?", "Is training free?"],
    },
  },
  {
    keywords: ["nti", "المعهد القومي للاتصالات", "القومي للاتصالات"],
    answer: {
      ar: "المعهد القومي للاتصالات (**NTI**) هو جهة تدريبية حكومية تابعة لوزارة الاتصالات وتكنولوجيا المعلومات، بيقدم برامج متخصصة في:\n\n- **الشبكات وهندسة الاتصالات** (Cisco, 5G, Fiber Optics)\n- **الأمن السيبراني** (Cybersecurity Fundamentals & Operations)\n- **الحوسبة السحابية والأنظمة المدمجة (Embedded Systems)**\n\n**شروط التقديم:** خريجو كليات الهندسة، الحاسبات والمعلومات، والعلوم، والتخصصات ذات الصلة، والتقديم متاح من خلال موقع المعهد الرسمي.",
      en: "The National Telecommunication Institute (**NTI**) is an institute under the Ministry of Communications specializing in:\n\n- **Networks and Telecom Engineering** (Cisco, 5G, Fiber Optics)\n- **Cybersecurity** (Fundamentals & Operations)\n- **Cloud Computing & Embedded Systems**\n\n**Admission:** Graduates in Engineering, Computer Science, Science, and related degrees via the official NTI portal.",
    },
    sourceIds: ["src-4", "src-6"],
    suggestions: {
      ar: ["إيه تراكات NTI المتاحة؟", "طب إيه الأوراق المطلوبة لـ NTI؟", "هل في اختبار قبول في NTI؟", "مدة التدريب في NTI كام؟"],
      en: ["What NTI tracks are available?", "What documents are required for NTI?", "Is there an NTI admission test?", "How long is NTI training?"],
    },
  },
  {
    keywords: ["depi", "رواد مصر الرقمية", "ديبي"],
    answer: {
      ar: "مبادرة **رواد مصر الرقمية (DEPI)** هي مبادرة تابعة لوزارة الاتصالات بتقدم 6 تراكات رئيسية بالتعاون مع شركات عالمية:\n\n1. **Software Development** (DevOps, React, .NET, Testing)\n2. **AI & Data Science**\n3. **Data Analytics**\n4. **Digital Arts & Design**\n5. **Infrastructure & Cybersecurity**\n6. **Management & ERP (SAP, CRM)**\n\nالتدريب مجاني ومتاح لطلاب السنوات النهائية والخريجين من مختلف الجامعات المصرية.",
      en: "**Digital Egypt Pioneers Initiative (DEPI)** offers 6 main tracks with global industry leaders:\n\n1. **Software Development** (DevOps, React, .NET, QA)\n2. **AI & Data Science**\n3. **Data Analytics**\n4. **Digital Arts & Design**\n5. **Infrastructure & Cybersecurity**\n6. **Management & ERP (SAP, CRM)**\n\nTraining is free for final-year students and university graduates.",
    },
    sourceIds: ["src-3"],
    suggestions: {
      ar: ["إيه شروط القبول في DEPI؟", "كام ساعة تدريب في تراك React في DEPI؟", "هل التدريب في DEPI أونلاين ولا حضور؟"],
      en: ["What are DEPI admission requirements?", "How many hours is React track in DEPI?", "Is DEPI online or offline?"],
    },
  },
  {
    keywords: ["iti", "معهد تكنولوجيا المعلومات"],
    answer: {
      ar: "معهد تكنولوجيا المعلومات (**ITI**) بيقدم أشهر وأقوى المنح التدريبية المتخصصة في مصر، وأبرزها:\n\n- **منحة الـ 9 شهور الاحترافية** (Professional Training Program)\n- **منحة الـ 3 شهور المكثفة** (Intensive Code Camp)\n- **مبادرات التدريب الصيفي وسفراء التكنولوجيا**\n\n**شروط القبول:** تفرغ كامل، اجتياز اختبارات القبول (IQ، English، Technical)، واجتياز المقابلة الشخصية.",
      en: "**Information Technology Institute (ITI)** provides leading tech scholarships in Egypt, including:\n\n- **9-Month Professional Training Program**\n- **3-Month Intensive Code Camp**\n- **Summer training & University initiatives**\n\n**Requirements:** Full-time dedication, passing admission exams (IQ, English, Tech), and personal interview.",
    },
    sourceIds: ["src-1"],
    suggestions: DEFAULT_SUGGESTIONS,
  },
  {
    keywords: ["مدة", "كام شهر", "ساعات", "كام ساعة", "duration", "how long", "hours"],
    answer: {
      ar: "تختلف مدة التدريب حسب كل جهة وبرنامج:\n\n- **ITI:** تتراوح بين **3 شهور** (المعسكرات المكثفة) إلى **9 شهور** (البرنامج الاحترافي الشامل).\n- **NTI:** تتراوح البرامج بين **شهرين إلى 4 شهور** تدريب مكثف (حوالي 120 إلى 240 ساعة).\n- **DEPI:** برامج ممتدة على مدار **6 شهور** مقسمة على مراحل تدريبية وتطبيق عملي.",
      en: "Training duration depends on the institution and program:\n\n- **ITI:** Ranges from **3 months** (Intensive Code Camp) to **9 months** (Professional Diploma).\n- **NTI:** Typically **2 to 4 months** of intensive training (120 - 240 hours).\n- **DEPI:** **6-month** structured programs with practical projects.",
    },
    sourceIds: ["src-1", "src-3", "src-4"],
    suggestions: {
      ar: ["هل التدريب صباحي ولا مسائي؟", "هل الحضور إجباري؟", ...DEFAULT_SUGGESTIONS.ar.slice(0, 2)],
      en: ["Are classes morning or evening?", "Is attendance mandatory?", ...DEFAULT_SUGGESTIONS.en.slice(0, 2)],
    },
  },
  {
    keywords: ["ورق", "اوراق", "أوراق", "مستندات", "documents", "papers", "requirements documents"],
    answer: {
      ar: "الأوراق والمستندات المطلوبة للتقديم غالباً ما تشمل:\n\n1. صورة بطاقة الرقم القومي (سارية)\n2. أصل أو صورة طبق الأصل من شهادة التخرج\n3. شهادة الموقف من التجنيد (للذكور)\n4. السيرة الذاتية (CV) الحديثة\n5. صور شخصية حديثة\n6. بيان درجات تراكمي (في بعض البرامج المتخصصة)",
      en: "Typical required application documents include:\n\n1. Valid National ID copy\n2. Graduation Certificate / Degree transcript\n3. Military status certificate (for males)\n4. Updated Resume / CV\n5. Recent personal photos\n6. Academic transcript (for specific programs)",
    },
    sourceIds: ["src-1", "src-6"],
    suggestions: {
      ar: ["هل في اختبار قبول؟", "إمتى التقديم القادم؟", "هل التدريب مجاني؟"],
      en: ["Is there an admission exam?", "When is the next round?", "Is training free?"],
    },
  },
  {
    keywords: ["امتحان", "اختبار", "انترفيو", "مقابلة", "interview", "test", "exam"],
    answer: {
      ar: "نعم، معظم البرامج تشتمل على مراحل تقييم لضمان الجدية والجاهزية:\n\n1. **اختبار لغة إنجليزية (English Test):** لتقييم مهارات القراءة والاستيعاب.\n2. **اختبار قدرات وذكاء (IQ Test):** للتفكير المنطقي وحل المشكلات.\n3. **اختبار تقني أساسي (Technical Test):** في أساسيات المسار المختار.\n4. **مقابلة شخصية (Soft Skills / Technical Interview):** للتعرف على أهدافك والتزامك.",
      en: "Yes, most programs involve admission screening steps:\n\n1. **English Assessment Test**\n2. **Logical Thinking & IQ Test**\n3. **Basic Technical Assessment**\n4. **Personal & Technical Interview**",
    },
    sourceIds: ["src-1", "src-6"],
    suggestions: DEFAULT_SUGGESTIONS,
  },
  {
    keywords: ["مجاني", "فلوس", "رسوم", "تكلفة", "free", "fees", "cost", "paid"],
    answer: {
      ar: "أغلب البرامج التدريبية التي تقدمها **ITI** و**NTI** و**DEPI** و**MCIT** هي **منح مجانية تماماً بالكامل (100%)** ممولة من وزارة الاتصالات وتكنولوجيا المعلومات لدعم وتمكين الكوادر والشباب في مصر.",
      en: "Most programs offered by **ITI**, **NTI**, **DEPI**, and **MCIT** are **100% free government scholarships** funded by the Ministry of Communications and Information Technology.",
    },
    sourceIds: ["src-2", "src-3"],
    suggestions: {
      ar: ["إيه البرامج المتاحة حالياً؟", "هل التدريب بيدي شهادة معتمدة؟", ...DEFAULT_SUGGESTIONS.ar.slice(0, 2)],
      en: ["Which programs are available?", "Does training include a certificate?", ...DEFAULT_SUGGESTIONS.en.slice(0, 2)],
    },
  },
  {
    keywords: ["ذكاء اصطناعي", "ai", "تعلم الآلة", "artificial intelligence", "machine learning"],
    answer: {
      ar: "لو مهتم بمسار **الذكاء الاصطناعي (AI & Data Science)**، في خيارات ممتازة:\n\n- **DEPI:** مسار AI & Data Science بالتعاون مع جهات عالمية لتعلم Python، Machine Learning، والـ Deep Learning.\n- **ITI:** دبلومة الذكاء الاصطناعي وتعلم الآلة الشاملة (9 شهور أو 3 شهور).\n- **NTI:** مسارات تحليل البيانات وتعلم الآلة التطبيقي.",
      en: "For **Artificial Intelligence & Data Science**, top pathways include:\n\n- **DEPI:** AI & Data Science track with industry leaders covering Python, ML, and Deep Learning.\n- **ITI:** Comprehensive AI diploma (9 months or 3 months intensive).\n- **NTI:** Applied Machine Learning and Data Analysis tracks.",
    },
    sourceIds: ["src-1", "src-3"],
    suggestions: {
      ar: ["إيه المهارات المطلوبة قبل البدء؟", "إيه الفرق بين Data Science و AI؟", ...DEFAULT_SUGGESTIONS.ar.slice(0, 2)],
      en: ["What skills do I need before starting?", "Difference between Data Science & AI?", ...DEFAULT_SUGGESTIONS.en.slice(0, 2)],
    },
  },
  {
    keywords: ["تجارة", "خريج", "غير تقني", "مش تقني", "business", "commerce", "non technical", "non-technical"],
    answer: {
      ar: "خريجو التخصصات غير التقنية زي **التجارة** أو **الآداب** أو **الحقوق** يقدروا يبدأوا في مسارات متميزة جداً ومطلوبة في سوق العمل، زي:\n\n- **تحليل البيانات (Data Analysis & Power BI)**\n- **تطوير الويب (Frontend Development)**\n- **إدارة المشاريع الرقمية والأنظمة المؤسسية (ERP / SAP)**\n- **التسويق الرقمي والعمل الحر (Freelancing via ITIDA)**",
      en: "Graduates with non-technical backgrounds like **Business**, **Arts**, or **Law** can excel in top in-demand tracks:\n\n- **Data Analysis & Business Intelligence**\n- **Frontend Web Development**\n- **ERP & Enterprise Systems (SAP, CRM)**\n- **Digital Freelancing (via ITIDA)**",
    },
    sourceIds: ["src-2", "src-3"],
    suggestions: {
      ar: ["إيه أنسب مسار ليا كمبتدئ؟", "محتاج أتعلم إيه الأول؟", ...DEFAULT_SUGGESTIONS.ar.slice(0, 2)],
      en: ["Which track fits me as a beginner?", "What should I learn first?", ...DEFAULT_SUGGESTIONS.en.slice(0, 2)],
    },
  },
];


function hashSeed(str: string) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h;
}

const NO_INFO: LocalizedText = {
  ar: "مش لاقي معلومات موثوقة كفاية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة. ممكن تحاول توضح سؤالك أكتر، أو تسأل عن مؤسسة أو برنامج معين زي ITI أو NTI أو DEPI؟",
  en: "I cannot find enough reliable information in the available sources to answer that accurately. Try clarifying your question, or ask about a specific institution or program such as ITI, NTI, or DEPI.",
};

const GENERAL_ANSWER: LocalizedText = {
  ar: "شكرا لسؤالك. بناء على المصادر المتاحة، فيه معلومات عامة بتساعدك تبدأ:\n\n- في أكتر من جهة تدريب تقني موثوقة في مصر زي **ITI** و**NTI** و**DEPI** و**MCIT** و**ITIDA**\n- كل جهة بتقدم مسارات مختلفة حسب المستوى والتخصص\n- ممكن تسألني عن مؤسسة أو مسار معين عشان أديك تفاصيل أدق\n\nعايز أساعدك تختار المسار المناسب ليك؟",
  en: "Thanks for your question. Based on the available sources, here are useful starting points:\n\n- Egypt has several trusted technology training institutions such as **ITI**, **NTI**, **DEPI**, **MCIT**, and **ITIDA**\n- Each institution offers different tracks depending on level and specialization\n- You can ask about a specific institution or track for more precise details\n\nWould you like help choosing a suitable path?",
};

export function generateMockResponse(
  message: string,
  language: Language = "ar",
  history: { role: string; content: string }[] = []
): ChatApiResponse {
  const normalized = message.toLowerCase();

  // 1. Direct memory inquiry about conversation history
  const isFirstQInquiry =
    normalized.includes("أول سؤال") ||
    normalized.includes("اول سؤال") ||
    normalized.includes("سألتك عن إيه") ||
    normalized.includes("سالتك عن ايه") ||
    normalized.includes("first question") ||
    normalized.includes("what did i ask");

  if (isFirstQInquiry && history.length > 0) {
    const userTurns = history.filter((h) => h.role === "user");
    if (userTurns.length > 0) {
      const firstQ = userTurns[0].content;
      return {
        answer:
          language === "ar"
            ? `أول سؤال سألتهولي كان: **"${firstQ}"** 💬`
            : `The first question you asked was: **"${firstQ}"** 💬`,
        sources: [],
        suggested_questions:
          language === "ar"
            ? ["طب إيه تفاصيل برامج NTI؟", "إيه شروط التقديم في ITI؟", "هل التدريب مجاني؟"]
            : ["Tell me about NTI tracks", "What are ITI admission requirements?", "Is training free?"],
      };
    }
  }

  // 2. Follow-up resolution: check if current question has pronouns ("فيها", "شروطها", "عنها") and blend previous topic
  let searchTarget = normalized;
  const isFollowUp =
    normalized.includes("فيها") ||
    normalized.includes("عنها") ||
    normalized.includes("شروطها") ||
    normalized.includes("مدتها") ||
    normalized.split(/\s+/).length <= 3;

  if (isFollowUp && history.length > 0) {
    const prevUserMsg = [...history].reverse().find((h) => h.role === "user")?.content.toLowerCase() ?? "";
    searchTarget = `${prevUserMsg} ${normalized}`;
  }

  const matched = rules.find((rule) => rule.keywords.some((k) => searchTarget.includes(k)));

  if (matched) {
    return {
      answer: matched.answer[language],
      sources: sources.filter((s) => matched.sourceIds.includes(s.id)),
      suggested_questions: matched.suggestions[language],
    };
  }

  // Low-confidence fallback that avoids hallucination.
  const seed = hashSeed(message) % 3;
  if (seed === 0) {
    return {
      answer: NO_INFO[language],
      sources: [],
      suggested_questions: [
        language === "ar" ? "إيه شروط التقديم في ITI؟" : "What are the ITI admission requirements?",
        language === "ar" ? "إيه أفضل مسار للذكاء الاصطناعي؟" : "What is the best AI track?",
        language === "ar" ? "هل التدريب مجاني؟" : "Is the training free?",
      ],
    };
  }

  return {
    answer: GENERAL_ANSWER[language],
    sources: sources.slice(0, 2),
    suggested_questions: DEFAULT_SUGGESTIONS[language],
  };
}

