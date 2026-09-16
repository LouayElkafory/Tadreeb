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
    keywords: ["iti", "شروط", "تقديم", "requirements", "admission", "apply"],
    answer: {
      ar: "بشكل عام، التقديم في **ITI** بيكون متاح لخريجي الجامعات وطلاب السنة النهائية في تخصصات مرتبطة بالحاسب والهندسة والعلوم.\n\nالخطوات الأساسية بتشمل:\n\n1. التسجيل من خلال الموقع الرسمي في فترة التقديم المعلنة\n2. اجتياز اختبار تحديد المستوى\n3. اجتياز المقابلة الشخصية\n\nلو عايز تعرف تفاصيل أكتر عن برنامج معين أو موعد التقديم القادم، قولي وهدور لك في المصادر.",
      en: "In general, **ITI** applications are available for university graduates and final-year students in computer science, engineering, science, and related fields.\n\nThe basic steps usually include:\n\n1. Registering through the official website during the announced application period\n2. Passing a placement or admission test\n3. Passing the personal interview\n\nIf you want details about a specific program or the next application window, tell me and I will check the sources.",
    },
    sourceIds: ["src-1", "src-6"],
    suggestions: DEFAULT_SUGGESTIONS,
  },
  {
    keywords: ["مجاني", "فلوس", "رسوم", "تكلفة", "free", "fees", "cost", "paid"],
    answer: {
      ar: "أغلب البرامج التدريبية اللي بتقدمها جهات زي **ITI** و**NTI** و**DEPI** مجانية للطلاب المقبولين، لأنها جزء من مبادرات لدعم التحول الرقمي وتنمية المهارات.\n\nمع ذلك، بعض البرامج المتخصصة أو الشراكات مع شركات معينة ممكن يكون ليها شروط مختلفة، فالأفضل دايما تتأكد من صفحة البرنامج قبل التقديم.",
      en: "Most training programs offered by institutions such as **ITI**, **NTI**, and **DEPI** are free for accepted learners because they are part of national digital skills initiatives.\n\nSome specialized programs or company partnerships may have different conditions, so it is always best to confirm on the program page before applying.",
    },
    sourceIds: ["src-2", "src-3"],
    suggestions: {
      ar: ["إيه البرامج المجانية المتاحة؟", "هل التدريب المجاني بيدي شهادة معتمدة؟", ...DEFAULT_SUGGESTIONS.ar.slice(0, 2)],
      en: ["Which free programs are available?", "Does free training include a certificate?", ...DEFAULT_SUGGESTIONS.en.slice(0, 2)],
    },
  },
  {
    keywords: ["ذكاء اصطناعي", "ai", "تعلم الآلة", "artificial intelligence", "machine learning"],
    answer: {
      ar: "لو مهتم بمسار **الذكاء الاصطناعي**، في أكتر من خيار حسب مستواك:\n\n- **للمبتدئين:** برامج تمهيدية في أساسيات البرمجة وتحليل البيانات\n- **للمتوسط:** مسارات في تعلم الآلة وPython\n- **للمتقدم:** برامج متخصصة في التعلم العميق ومعالجة اللغة الطبيعية\n\nبرنامج **ITI للذكاء الاصطناعي المتقدم** من أشهر أمثلة المسار المتقدم.",
      en: "If you are interested in **Artificial Intelligence**, there are options depending on your current level:\n\n- **Beginner:** foundations in programming and data analysis\n- **Intermediate:** machine learning and Python tracks\n- **Advanced:** deep learning and natural language processing programs\n\nThe **ITI Advanced Artificial Intelligence Program** is one of the well-known advanced examples.",
    },
    sourceIds: ["src-1", "src-3"],
    suggestions: {
      ar: ["إيه المهارات المطلوبة قبل البدء؟", "إيه الفرق بين ML و Deep Learning؟", ...DEFAULT_SUGGESTIONS.ar.slice(0, 2)],
      en: ["What skills do I need before starting?", "What is the difference between ML and deep learning?", ...DEFAULT_SUGGESTIONS.en.slice(0, 2)],
    },
  },
  {
    keywords: ["تجارة", "خريج", "غير تقني", "مش تقني", "business", "commerce", "non technical", "non-technical"],
    answer: {
      ar: "خريجي التخصصات غير التقنية زي التجارة أو الآداب يقدروا يبدأوا من مسارات مناسبة كبداية، زي:\n\n- **تحليل البيانات**\n- **إدارة المشاريع الرقمية**\n- **أساسيات البرمجة**\n\nبرامج زي **أساسيات التحول الرقمي** من MCIT ممكن تكون خطوة أولى قبل التخصص أكتر.",
      en: "Graduates from non-technical backgrounds such as business or humanities can start with beginner-friendly tracks, such as:\n\n- **Data analysis**\n- **Digital project management**\n- **Programming foundations**\n\nPrograms such as **Digital Transformation Foundations** from MCIT can be a useful first step before specializing further.",
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

export function generateMockResponse(message: string, language: Language = "ar"): ChatApiResponse {
  const normalized = message.toLowerCase();
  const matched = rules.find((rule) => rule.keywords.some((k) => normalized.includes(k)));

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
