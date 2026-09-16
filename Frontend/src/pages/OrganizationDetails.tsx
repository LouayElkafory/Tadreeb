import { Link, useParams, Navigate } from "react-router-dom";
import { ArrowLeft, Sparkles } from "lucide-react";
import { organizations } from "../data/organizations";
import { programs, tracks } from "../data/programs";
import ProgramCard from "../components/ProgramCard";
import OrganizationCard from "../components/OrganizationCard";
import { useLanguage } from "../hooks/useLanguage";

export default function OrganizationDetails() {
  const { id } = useParams();
  const org = organizations.find((o) => o.id === id);
  const { localize, t } = useLanguage();

  if (!org) return <Navigate to="/organizations" replace />;

  const orgPrograms = programs.filter((p) => p.organization === org.id);
  const related = organizations.filter((o) => o.id !== org.id).slice(0, 3);

  return (
    <div className="max-w-5xl mx-auto px-5 py-14 sm:py-16">
      <Link to="/organizations" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-primary mb-8">
        <ArrowLeft size={15} className="rotate-180 rtl:rotate-0" />
        {t("organizations.back")}
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center gap-5 mb-6">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-base shrink-0"
          style={{ backgroundColor: org.color }}
        >
          {org.shortName}
        </div>
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-deep-navy">{localize(org.name)}</h1>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {org.categories.map((c) => (
              <span key={c.en} className="px-2.5 py-1 rounded-full text-xs font-medium bg-baby-blue text-primary-dark">
                {localize(c)}
              </span>
            ))}
          </div>
        </div>
      </div>

      <p className="text-text-secondary text-base leading-relaxed max-w-2xl mb-8">{localize(org.description)}</p>

      <Link
        to="/chat"
        state={{ prefill: t("organizations.askPrompt", { organization: org.shortName }), autoSend: true }}
        className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-bold text-white bg-primary hover:bg-primary-dark shadow-sm transition-colors mb-14"
      >
        <Sparkles size={16} />
        {t("organizations.ask")}
      </Link>

      <div className="mb-16">
        <h2 className="text-xl font-bold text-deep-navy mb-5">{t("organizations.availablePrograms")}</h2>
        {orgPrograms.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {orgPrograms.map((p) => (
              <ProgramCard key={p.id} program={p} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-text-secondary">
            {t("organizations.noPrograms")}
          </p>
        )}
      </div>

      <div className="mb-4">
        <h2 className="text-xl font-bold text-deep-navy mb-5">{t("organizations.relatedTracks")}</h2>
        <div className="flex flex-wrap gap-2">
          {tracks
            .filter((t) => orgPrograms.some((p) => p.track === t.id))
            .map((t) => (
              <span key={t.id} className="px-3 py-1.5 rounded-full text-sm font-medium bg-soft-blue/60 text-deep-navy">
                {localize(t.name)}
              </span>
            ))}
        </div>
      </div>

      <div className="mt-16">
        <h2 className="text-xl font-bold text-deep-navy mb-5">{t("organizations.other")}</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {related.map((o) => (
            <OrganizationCard key={o.id} org={o} />
          ))}
        </div>
      </div>
    </div>
  );
}
