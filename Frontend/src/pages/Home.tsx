import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ShieldCheck,
  Search,
  Sparkles,
  MessageCircleQuestion,
  ListChecks,
  Building2,
} from "lucide-react";
import ChatInput from "../components/ChatInput";
import SuggestedQuestions from "../components/SuggestedQuestions";
import OrganizationCard from "../components/OrganizationCard";
import { organizations } from "../data/organizations";
import { tracks } from "../data/programs";
import { useLanguage } from "../hooks/useLanguage";

const HOW_IT_WORKS = [
  { icon: MessageCircleQuestion, titleKey: "home.how.1.title", descKey: "home.how.1.desc" },
  { icon: Search, titleKey: "home.how.2.title", descKey: "home.how.2.desc" },
  { icon: Sparkles, titleKey: "home.how.3.title", descKey: "home.how.3.desc" },
  { icon: ListChecks, titleKey: "home.how.4.title", descKey: "home.how.4.desc" },
];

export default function Home() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { localize, t } = useLanguage();
  const heroSuggestions = [
    t("hero.suggestion.iti"),
    t("hero.suggestion.business"),
    t("hero.suggestion.free"),
    t("hero.suggestion.ai"),
  ];

  const handleAsk = (text?: string) => {
    const message = (text ?? query).trim();
    if (!message) {
      navigate("/chat");
      return;
    }
    navigate("/chat", { state: { prefill: message, autoSend: true } });
  };

  return (
    <div className="overflow-x-clip">
      {/* HERO */}
      <section className="relative">
        <div
          className="relative min-h-[640px] sm:min-h-[720px] flex items-center bg-cover bg-no-repeat"
          style={{
            backgroundImage: "url(/main.png)",
            backgroundPosition: "center 30%",
          }}
        >
          {/* mask the embedded nav strip baked into the artwork */}
          <div className="absolute inset-x-0 top-0 h-24 sm:h-28 bg-gradient-to-b from-[#050505] via-[#050505]/70 to-transparent pointer-events-none" />
          {/* soft bottom fade into page background */}
          <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#050505] to-transparent pointer-events-none" />

          <div className="relative z-10 w-full max-w-6xl mx-auto px-5 pt-16 sm:pt-10">
            <div className="max-w-xl animate-fade-up">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur text-primary-dark text-xs font-semibold shadow-sm mb-5">
                <ShieldCheck size={14} />
                {t("hero.trust")}
              </span>
              <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-extrabold leading-[1.25] text-deep-navy mb-4">
                {t("hero.headline")}
              </h1>
              <p className="text-base sm:text-lg text-text-secondary leading-relaxed mb-7 max-w-lg">
                {t("hero.body")}
              </p>

              <div className="max-w-lg mb-4">
                <ChatInput
                  value={query}
                  onChange={setQuery}
                  onSubmit={() => handleAsk()}
                  size="lg"
                  placeholder={t("hero.placeholder")}
                />
              </div>

              <div className="mb-8 max-w-lg">
                <SuggestedQuestions questions={heroSuggestions} onSelect={(q) => handleAsk(q)} />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => handleAsk()}
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full text-sm font-bold text-white bg-primary hover:bg-primary-dark shadow-lg shadow-primary/25 transition-all hover:-translate-y-0.5"
                >
                  {t("common.startChat")}
                  <ArrowLeft size={16} className="rtl:rotate-180" />
                </button>
                <button
                  onClick={() => navigate("/programs")}
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full text-sm font-bold text-deep-navy bg-white/80 backdrop-blur hover:bg-white shadow-sm transition-all"
                >
                  {t("common.explorePrograms")}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST / EXPLANATION */}
      <section className="max-w-6xl mx-auto px-5 py-20 sm:py-24">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-deep-navy mb-4">
            {t("home.trustTitle")}
          </h2>
          <p className="text-text-secondary text-base leading-relaxed">
            {t("home.trustBody")}
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {[
            { label: t("home.step.question"), icon: MessageCircleQuestion },
            { label: t("home.step.search"), icon: Search },
            { label: t("home.step.answer"), icon: Sparkles },
            { label: t("home.step.sources"), icon: ListChecks },
          ].map((step, i) => (
            <div key={step.label} className="relative flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-2xl bg-baby-blue text-primary flex items-center justify-center mb-3">
                <step.icon size={22} />
              </div>
              <span className="text-sm font-semibold text-deep-navy">{step.label}</span>
              {i < 3 && (
                <span className="hidden md:block absolute top-7 start-[calc(100%-0.5rem)] w-[calc(100%-2.5rem)] border-t-2 border-dashed border-soft-blue" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ORGANIZATIONS PREVIEW */}
      <section className="bg-baby-blue/40 py-20 sm:py-24">
        <div className="max-w-6xl mx-auto px-5">
          <div className="flex items-end justify-between mb-10 flex-wrap gap-4">
            <div>
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary mb-2">
                <Building2 size={14} />
                {t("home.orgEyebrow")}
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-deep-navy">{t("home.orgTitle")}</h2>
            </div>
            <button
              onClick={() => navigate("/organizations")}
              className="text-sm font-semibold text-primary hover:text-primary-dark inline-flex items-center gap-1.5"
            >
              {t("home.orgViewAll")}
              <ArrowLeft size={15} className="rtl:rotate-180" />
            </button>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {organizations.map((org) => (
              <OrganizationCard key={org.id} org={org} />
            ))}
          </div>
        </div>
      </section>

      {/* TRAINING TRACKS PREVIEW */}
      <section className="max-w-6xl mx-auto px-5 py-20 sm:py-24">
        <div className="text-center max-w-xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-deep-navy mb-3">{t("home.tracksTitle")}</h2>
          <p className="text-text-secondary">{t("home.tracksBody")}</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {tracks.map((track) => (
            <div
              key={track.id}
              className="group flex flex-col p-6 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:shadow-lg transition-all"
            >
              <div className="w-11 h-11 rounded-xl bg-baby-blue text-primary flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-colors">
                <Sparkles size={19} />
              </div>
              <h3 className="text-base font-bold text-deep-navy mb-1.5">{localize(track.name)}</h3>
              <p className="text-sm text-text-secondary leading-relaxed mb-5 flex-1">{localize(track.description)}</p>
              <button
                onClick={() => handleAsk(t("home.askTrackPrompt", { track: localize(track.name) }))}
                className="self-start text-sm font-semibold text-primary hover:text-primary-dark inline-flex items-center gap-1.5"
              >
                {t("home.askTrack")}
                <ArrowLeft size={14} className="rtl:rotate-180" />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-deep-navy py-20 sm:py-24">
        <div className="max-w-6xl mx-auto px-5">
          <div className="text-center max-w-xl mx-auto mb-14">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">{t("home.howTitle")}</h2>
            <p className="text-white/60">{t("home.howBody")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map((step, i) => (
              <div key={step.titleKey} className="relative">
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold shrink-0">
                    {i + 1}
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-white/10 text-sky-blue flex items-center justify-center">
                    <step.icon size={18} />
                  </div>
                </div>
                <h3 className="text-white font-bold mb-1.5">{t(step.titleKey)}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{t(step.descKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="max-w-6xl mx-auto px-5 py-20 sm:py-24">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-primary-dark px-8 py-14 sm:py-16 text-center">
          <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, white 0%, transparent 35%)" }} />
          <div className="relative">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">{t("home.finalTitle")}</h2>
            <p className="text-white/80 text-base mb-8 max-w-md mx-auto">
              {t("home.finalBody")}
            </p>
            <button
              onClick={() => navigate("/chat")}
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold text-primary-dark bg-white hover:bg-baby-blue shadow-lg transition-all hover:-translate-y-0.5"
            >
              {t("common.startChat")}
              <ArrowLeft size={16} className="rtl:rotate-180" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
