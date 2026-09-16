import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";
import type { Program } from "../types";
import { organizations } from "../data/organizations";
import { tracks } from "../data/programs";
import { useLanguage } from "../hooks/useLanguage";

export default function ProgramCard({ program }: { program: Program }) {
  const org = organizations.find((o) => o.id === program.organization);
  const track = tracks.find((t) => t.id === program.track);
  const { localize, t } = useLanguage();
  const programName = localize(program.name);

  return (
    <div className="flex flex-col p-5 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-baby-blue text-primary-dark">
          {track ? localize(track.name) : ""}
        </span>
        <span className="text-xs font-medium text-text-secondary">{t(`level.${program.level}`)}</span>
      </div>
      <h3 className="text-base font-bold text-deep-navy mb-1.5 leading-snug">{programName}</h3>
      <p className="text-xs font-medium text-primary mb-2">{org?.shortName}</p>
      <p className="text-sm text-text-secondary leading-relaxed mb-4 flex-1">{localize(program.description)}</p>
      {program.skills && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {program.skills.slice(0, 3).map((skill) => (
            <span key={skill} className="px-2 py-0.5 rounded-md text-[11px] bg-soft-blue/60 text-deep-navy">
              {skill}
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2 mt-auto pt-1">
        <Link
          to={`/programs/${program.id}`}
          className="flex-1 text-center px-3 py-2.5 rounded-xl text-sm font-semibold text-deep-navy bg-baby-blue hover:bg-soft-blue transition-colors"
        >
          {t("common.details")}
        </Link>
        <Link
          to="/chat"
          state={{ prefill: t("programs.cardAskPrompt", { program: programName }) }}
          className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary-dark transition-colors shrink-0"
          aria-label={t("programs.ask")}
        >
          <Sparkles size={14} />
        </Link>
      </div>
    </div>
  );
}
