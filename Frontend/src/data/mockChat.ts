import type { ChatApiResponse } from "../types";
import { sources } from "./sources";

const DEFAULT_SUGGESTIONS = [
  "طب إيه الأوراق المطلوبة؟",
  "هل في اختبار قبول؟",
  "مدة التدريب كام؟",
  "إمتى التقديم؟",
];

interface Rule {
  keywords: string[];
  answer: string;
  sourceIds: string[];
  suggestions: string[];
}

const rules: Rule[] = [
  {
    keywords: ["iti", "شروط", "تقديم"],
    answer:
      "بشكل عام، التقديم في **ITI** بيكون متاح لخريجي الجامعات وطلاب السنة النهائية في تخصصات مرتبطة بالحاسب والهندسة والعلوم.\n\nالخطوات الأساسية بتشمل:\n\n1. التسجيل من خلال الموقع الرسمي في فترة التقديم المعلنة\n2. اجتياز اختبار تحديد المستوى\n3. اجتياز المقابلة الشخصية\n\nلو عايز تعرف تفاصيل أكتر عن برنامج معين أو موعد التقديم القادم، قولي وهدور لك في المصادر.",
    sourceIds: ["src-1", "src-6"],
    suggestions: DEFAULT_SUGGESTIONS,
  },
  {
    keywords: ["مجاني", "فلوس", "رسوم", "تكلفة"],
    answer:
      "أغلب البرامج التدريبية اللي بتقدمها جهات زي **ITI** و**NTI** و**DEPI** مجانية تمامًا للطلاب المقبولين، لأنها جزء من مبادرات حكومية لدعم التحول الرقمي.\n\nمع ذلك، بعض البرامج المتخصصة أو الشراكات مع شركات معينة ممكن يكون ليها شروط مختلفة، فالأفضل دايمًا تتأكد من صفحة البرنامج قبل التقديم.",
    sourceIds: ["src-2", "src-3"],
    suggestions: ["إيه البرامج المجانية المتاحة؟", "هل التدريب المجاني بيدي شهادة معتمدة؟", ...DEFAULT_SUGGESTIONS.slice(0, 2)],
  },
  {
    keywords: ["ذكاء اصطناعي", "ai", "تعلم الآلة"],
    answer:
      "لو مهتم بمسار **الذكاء الاصطناعي**، في أكتر من خيار متاح حسب مستواك:\n\n- **للمبتدئين:** برامج تمهيدية في أساسيات البرمجة وتحليل البيانات\n- **للمتوسط:** مسارات في تعلم الآلة (Machine Learning) وبايثون\n- **للمتقدم:** برامج متخصصة في التعلم العميق (Deep Learning) ومعالجة اللغة الطبيعية\n\nبرنامج **ITI للذكاء الاصطناعي المتقدم** من أشهر الأمثلة على المسار المتقدم ده.",
    sourceIds: ["src-1", "src-3"],
    suggestions: ["إيه المهارات المطلوبة قبل البدء؟", "إيه الفرق بين ML و Deep Learning؟", ...DEFAULT_SUGGESTIONS.slice(0, 2)],
  },
  {
    keywords: ["تجارة", "خريج", "غير تقني", "مش تقني"],
    answer:
      "خريجي التخصصات غير التقنية زي التجارة أو الآداب مش لازم يكونوا خارج اللعبة! فيه مسارات مصممة خصيصًا كمدخل للمجال التقني زي:\n\n- **تحليل البيانات** (Data Analysis)\n- **إدارة المشاريع الرقمية**\n- **أساسيات البرمجة** كنقطة بداية\n\nبرامج زي **أساسيات التحول الرقمي** من MCIT بتكون مناسبة كخطوة أولى قبل التخصص أكتر.",
    sourceIds: ["src-2", "src-3"],
    suggestions: ["إيه أنسب مسار ليا كمبتدئ؟", "محتاج أتعلم إيه الأول؟", ...DEFAULT_SUGGESTIONS.slice(0, 2)],
  },
];

function hashSeed(str: string) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h;
}

export function generateMockResponse(message: string): ChatApiResponse {
  const normalized = message.toLowerCase();
  const matched = rules.find((rule) => rule.keywords.some((k) => normalized.includes(k)));

  if (matched) {
    return {
      answer: matched.answer,
      sources: sources.filter((s) => matched.sourceIds.includes(s.id)),
      suggested_questions: matched.suggestions,
    };
  }

  // Low-confidence fallback that avoids hallucination
  const seed = hashSeed(message) % 3;
  if (seed === 0) {
    return {
      answer:
        "مش لاقي معلومات موثوقة كفاية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة. ممكن تحاول توضح سؤالك أكتر، أو تسأل عن مؤسسة أو برنامج معين زي ITI أو NTI أو DEPI؟",
      sources: [],
      suggested_questions: [
        "إيه شروط التقديم في ITI؟",
        "إيه أفضل مسار للذكاء الاصطناعي؟",
        "هل التدريب مجاني؟",
      ],
    };
  }

  return {
    answer:
      `شكرًا لسؤالك. بناءً على المصادر المتاحة، فيه معلومات عامة بتساعدك تبدأ:\n\n- في أكتر من جهة تدريب تقني موثوقة في مصر زي **ITI** و**NTI** و**DEPI** و**MCIT**\n- كل جهة بتقدم مسارات مختلفة حسب المستوى والتخصص\n- ممكن تسألني عن مؤسسة أو مسار معين عشان أديك تفاصيل أدق\n\nعايز أساعدك تختار المسار المناسب ليك؟`,
    sources: sources.slice(0, 2),
    suggested_questions: DEFAULT_SUGGESTIONS,
  };
}
