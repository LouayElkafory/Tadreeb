import { Link } from "react-router-dom";
import { ArrowLeft, Building2 } from "lucide-react";
import type { Organization } from "../types";

export default function OrganizationCard({ org }: { org: Organization }) {
  return (
    <div className="group relative flex flex-col p-6 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-sm mb-4"
        style={{ backgroundColor: org.color }}
      >
        {org.shortName}
      </div>
      <h3 className="text-lg font-bold text-deep-navy mb-1.5">{org.name}</h3>
      <p className="text-sm text-text-secondary leading-relaxed mb-4 flex-1">{org.description}</p>
      <div className="flex flex-wrap gap-1.5 mb-5">
        {org.categories.map((cat) => (
          <span
            key={cat}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-baby-blue text-primary-dark"
          >
            {cat}
          </span>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-auto">
        <Link
          to={`/organizations/${org.id}`}
          className="flex-1 text-center px-4 py-2.5 rounded-xl text-sm font-semibold text-deep-navy bg-baby-blue hover:bg-soft-blue transition-colors"
        >
          اعرف أكتر
        </Link>
        <Link
          to="/chat"
          state={{ prefill: `احكيلي عن برامج ${org.shortName} وشروط التقديم.` }}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary-dark transition-colors"
        >
          اسأل AI
          <ArrowLeft size={14} className="rtl:rotate-180" />
        </Link>
      </div>
      <Building2 className="absolute top-5 end-5 text-soft-blue opacity-0 group-hover:opacity-100 transition-opacity" size={20} />
    </div>
  );
}
