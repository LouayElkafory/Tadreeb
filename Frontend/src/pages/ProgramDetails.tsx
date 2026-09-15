import { Link, Navigate, useParams } from "react-router-dom";
import { ArrowLeft, Sparkles, Info } from "lucide-react";
import { programs, tracks } from "../data/programs";
import { organizations } from "../data/organizations";
import ProgramCard from "../components/ProgramCard";

export default function ProgramDetails() {
  const { id } = useParams();
  const program = programs.find((p) => p.id === id);

  if (!program) return <Navigate to="/programs" replace />;

  const org = organizations.find((o) => o.id === program.organization);
  const track = tracks.find((t) => t.id === program.track);
  const related = programs.filter((p) => p.id !== program.id && p.track === program.track).slice(0, 3);

  return (
    <div className="max-w-4xl mx-auto px-5 py-14 sm:py-16">
      <Link to="/programs" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-primary mb-8">
        <ArrowLeft size={15} className="rotate-180 rtl:rotate-0" />
        رجوع للبرامج
      </Link>

      <div className="flex items-center gap-2 mb-4">
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-baby-blue text-primary-dark">{track?.name}</span>
        <span className="text-xs font-medium text-text-secondary">{program.level}</span>
      </div>

      <h1 className="text-2xl sm:text-3xl font-extrabold text-deep-navy mb-2">{program.name}</h1>
      <p className="text-sm font-semibold text-primary mb-6">{org?.name}</p>
      <p className="text-text-secondary text-base leading-relaxed max-w-2xl mb-8">{program.description}</p>

      <Link
        to="/chat"
        state={{ prefill: `إيه شروط التقديم في ${program.name}؟`, autoSend: true }}
        className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-bold text-white bg-primary hover:bg-primary-dark shadow-sm transition-colors mb-12"
      >
        <Sparkles size={16} />
        اسأل AI عن البرنامج
      </Link>

      <div className="grid sm:grid-cols-2 gap-6 mb-12">
        <div className="p-5 rounded-2xl border border-soft-blue bg-white">
          <h3 className="text-sm font-bold text-deep-navy mb-3">عن البرنامج</h3>
          <p className="text-sm text-text-secondary leading-relaxed">{program.description}</p>
        </div>
        <div className="p-5 rounded-2xl border border-soft-blue bg-white">
          <h3 className="text-sm font-bold text-deep-navy mb-3">المهارات المستهدفة</h3>
          {program.skills && program.skills.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {program.skills.map((skill) => (
                <span key={skill} className="px-2.5 py-1 rounded-md text-xs bg-soft-blue/60 text-deep-navy">
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-secondary">لا توجد بيانات متاحة حاليًا.</p>
          )}
        </div>
      </div>

      <div className="flex items-start gap-3 p-4 rounded-2xl bg-baby-blue/50 border border-soft-blue mb-12">
        <Info size={18} className="text-primary shrink-0 mt-0.5" />
        <p className="text-sm text-text-secondary leading-relaxed">
          لمعرفة تفاصيل زي مدة التدريب، شروط القبول الدقيقة، والمستندات المطلوبة،
          <Link to="/chat" state={{ prefill: `إيه شروط التقديم في ${program.name}؟`, autoSend: true }} className="text-primary font-semibold mx-1 hover:underline">
            اسأل المساعد
          </Link>
          لمعرفة التفاصيل المتاحة من المصادر الموثوقة.
        </p>
      </div>

      {related.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-deep-navy mb-5">برامج مشابهة</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {related.map((p) => (
              <ProgramCard key={p.id} program={p} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
