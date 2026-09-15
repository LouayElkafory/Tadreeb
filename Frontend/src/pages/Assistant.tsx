import { Link } from "react-router-dom";
import {
  ArrowLeft,
  BookOpenCheck,
  FileCheck2,
  Route,
  Building2,
  ListChecks,
  Clock,
  FileText,
  GitCompareArrows,
  Search,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

const CAN_HELP_WITH = [
  { icon: BookOpenCheck, label: "برامج التدريب" },
  { icon: FileCheck2, label: "شروط القبول" },
  { icon: Route, label: "المسارات التعليمية" },
  { icon: Building2, label: "المؤسسات التدريبية" },
  { icon: ListChecks, label: "أسئلة الأهلية" },
  { icon: Clock, label: "مدة التدريب" },
  { icon: FileText, label: "المستندات المطلوبة" },
  { icon: GitCompareArrows, label: "مقارنة المسارات" },
];

const STEPS = [
  { icon: Sparkles, title: "اسأل سؤالك", desc: "اكتب سؤالك عن التدريب التقني بشكل طبيعي." },
  { icon: Search, title: "استرجاع المعلومات", desc: "بندور في مصادر موثوقة عن أدق معلومة ليك." },
  { icon: BookOpenCheck, title: "توليد إجابة مبنية على مصادر", desc: "بنولّد إجابة واضحة بناءً على اللي لقيناه." },
  { icon: ShieldCheck, title: "عرض المصادر", desc: "بنوريك المصادر اللي اعتمدنا عليها في إجابتنا." },
];

export default function Assistant() {
  return (
    <div>
      <section className="bg-baby-blue/40 py-20 sm:py-24">
        <div className="max-w-3xl mx-auto px-5 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-deep-navy mb-4">
            مساعدك الذكي لاكتشاف فرص التدريب.
          </h1>
          <p className="text-text-secondary text-base sm:text-lg leading-relaxed mb-8 max-w-xl mx-auto">
            من أول سؤال لحد ما تعرف المسار المناسب ليك، تدريب بيساعدك تفهم اختياراتك من مصادر موثوقة.
          </p>
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold text-white bg-primary hover:bg-primary-dark shadow-lg shadow-primary/25 transition-all hover:-translate-y-0.5"
          >
            ابدأ المحادثة
            <ArrowLeft size={16} className="rtl:rotate-180" />
          </Link>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-5 py-20 sm:py-24">
        <h2 className="text-2xl font-extrabold text-deep-navy text-center mb-12">إيه اللي تدريب يقدر يساعدك فيه؟</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {CAN_HELP_WITH.map((item) => (
            <div
              key={item.label}
              className="flex flex-col items-center text-center gap-3 p-5 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:shadow-md transition-all"
            >
              <div className="w-11 h-11 rounded-xl bg-baby-blue text-primary flex items-center justify-center">
                <item.icon size={19} />
              </div>
              <span className="text-sm font-semibold text-deep-navy">{item.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-deep-navy py-20 sm:py-24">
        <div className="max-w-5xl mx-auto px-5">
          <h2 className="text-2xl font-extrabold text-white text-center mb-14">إزاي بيشتغل؟</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {STEPS.map((step, i) => (
              <div key={step.title}>
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold shrink-0">
                    {i + 1}
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-white/10 text-sky-blue flex items-center justify-center">
                    <step.icon size={18} />
                  </div>
                </div>
                <h3 className="text-white font-bold mb-1.5">{step.title}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-5 py-20 sm:py-24 text-center">
        <div className="w-14 h-14 rounded-2xl bg-baby-blue text-primary flex items-center justify-center mx-auto mb-6">
          <ShieldCheck size={24} />
        </div>
        <h2 className="text-2xl font-extrabold text-deep-navy mb-4">ليه المصادر مهمة؟</h2>
        <p className="text-text-secondary text-base leading-relaxed mb-10 max-w-xl mx-auto">
          تدريب بيجاوب بناءً على المعرفة المتاحة له، وبيكون شفاف معاك لو المعلومة مش موجودة بدل ما يختلق إجابة.
        </p>
        <p className="text-lg font-bold text-deep-navy mb-10">
          "لو مش لاقيين معلومات موثوقة كفاية، هنقولك بصراحة."
        </p>
        <Link
          to="/chat"
          className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold text-white bg-primary hover:bg-primary-dark shadow-sm transition-colors"
        >
          جرّب المساعد دلوقتي
          <ArrowLeft size={16} className="rtl:rotate-180" />
        </Link>
      </section>
    </div>
  );
}
