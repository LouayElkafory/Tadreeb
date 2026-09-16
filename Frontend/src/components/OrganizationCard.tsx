import { Link } from "react-router-dom";
import { ArrowLeft, Building2 } from "lucide-react";
import type { Organization } from "../types";
import { useLanguage } from "../hooks/useLanguage";

export default function OrganizationCard({ org }: { org: Organization }) {
  const { localize, t } = useLanguage();

  return (
    <div className="group relative flex flex-col p-6 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-sm mb-4"
        style={{ backgroundColor: org.color }}
      >
        {org.shortName}
      </div>
      <h3 className="text-lg font-bold text-deep-navy mb-1.5">{localize(org.name)}</h3>
      <p className="text-sm text-text-secondary leading-relaxed mb-4 flex-1">{localize(org.description)}</p>
      <div className="flex flex-wrap gap-1.5 mb-5">
        {org.categories.map((cat) => (
          <span
            key={cat.en}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-baby-blue text-primary-dark"
          >
            {localize(cat)}
          </span>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-auto">
        <Link
          to={`/organizations/${org.id}`}
          className="flex-1 text-center px-4 py-2.5 rounded-xl text-sm font-semibold text-deep-navy bg-baby-blue hover:bg-soft-blue transition-all duration-300 active:scale-95"
        >
          {t("common.learnMore")}
        </Link>
        <Link
          to="/chat"
          state={{ prefill: t("organizations.askPrompt", { organization: org.shortName }) }}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary-dark transition-all duration-300 active:scale-95"
        >
          {t("common.askAi")}
          <ArrowLeft size={14} className="rtl:rotate-180" />
        </Link>
      </div>
      <Building2 className="absolute top-5 end-5 text-soft-blue opacity-0 group-hover:opacity-100 transition-opacity" size={20} />
    </div>
  );
}
