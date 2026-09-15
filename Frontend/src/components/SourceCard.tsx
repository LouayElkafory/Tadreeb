import { ExternalLink, ShieldCheck, Landmark, FileText, Users } from "lucide-react";
import type { Source, SourceType } from "../types";

const TYPE_CONFIG: Record<SourceType, { label: string; icon: typeof ShieldCheck; className: string }> = {
  official: { label: "رسمي", icon: ShieldCheck, className: "bg-primary/10 text-primary" },
  government: { label: "حكومي", icon: Landmark, className: "bg-deep-navy/10 text-deep-navy" },
  document: { label: "مستند", icon: FileText, className: "bg-sky-blue/30 text-primary-dark" },
  community: { label: "مجتمعي", icon: Users, className: "bg-amber-100 text-amber-700" },
};

export default function SourceCard({ source }: { source: Source }) {
  const config = TYPE_CONFIG[source.type];
  const Icon = config.icon;

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block p-4 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:shadow-md transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="text-sm font-semibold text-deep-navy leading-snug group-hover:text-primary transition-colors line-clamp-2">
            {source.title}
          </h4>
          <p className="text-xs text-text-secondary mt-1">{source.organization}</p>
        </div>
        <ExternalLink size={16} className="text-text-secondary group-hover:text-primary shrink-0 mt-0.5" />
      </div>
      {source.description && (
        <p className="text-xs text-text-secondary mt-2 leading-relaxed line-clamp-2">{source.description}</p>
      )}
      <span
        className={`inline-flex items-center gap-1 mt-3 px-2.5 py-1 rounded-full text-[11px] font-semibold ${config.className}`}
      >
        <Icon size={12} />
        {config.label}
      </span>
    </a>
  );
}
