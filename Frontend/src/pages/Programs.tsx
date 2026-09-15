import { useMemo, useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import ProgramCard from "../components/ProgramCard";
import EmptyState from "../components/EmptyState";
import { programs, tracks } from "../data/programs";
import { organizations } from "../data/organizations";

const LEVELS = ["مبتدئ", "متوسط", "متقدم"] as const;

export default function Programs() {
  const [search, setSearch] = useState("");
  const [org, setOrg] = useState<string | null>(null);
  const [track, setTrack] = useState<string | null>(null);
  const [level, setLevel] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const filtered = useMemo(() => {
    return programs.filter((p) => {
      const matchesSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.description.toLowerCase().includes(search.toLowerCase());
      const matchesOrg = !org || p.organization === org;
      const matchesTrack = !track || p.track === track;
      const matchesLevel = !level || p.level === level;
      return matchesSearch && matchesOrg && matchesTrack && matchesLevel;
    });
  }, [search, org, track, level]);

  const clearFilters = () => {
    setSearch("");
    setOrg(null);
    setTrack(null);
    setLevel(null);
  };

  const hasFilters = !!(search || org || track || level);

  return (
    <div className="max-w-6xl mx-auto px-5 py-14 sm:py-16">
      <div className="text-center max-w-xl mx-auto mb-10">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-deep-navy mb-4">اكتشف مسارك التقني</h1>
        <p className="text-text-secondary text-base leading-relaxed">
          اختار مجال يهمك واسأل المساعد عن البرامج المناسبة ليك.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={17} className="absolute top-1/2 -translate-y-1/2 start-4 text-text-secondary" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="دور على برنامج أو مجال..."
            className="w-full ps-11 pe-4 py-3 rounded-2xl border border-soft-blue bg-white focus:border-primary outline-none text-sm text-deep-navy placeholder:text-text-secondary/70"
          />
        </div>
        <button
          onClick={() => setFiltersOpen((v) => !v)}
          className={`flex items-center justify-center gap-2 px-5 py-3 rounded-2xl text-sm font-semibold border transition-colors ${
            filtersOpen ? "bg-primary text-white border-primary" : "bg-white text-deep-navy border-soft-blue hover:border-primary"
          }`}
        >
          <SlidersHorizontal size={16} />
          فلاتر
        </button>
      </div>

      {filtersOpen && (
        <div className="grid sm:grid-cols-3 gap-3 mb-6 p-4 rounded-2xl bg-baby-blue/40 border border-soft-blue animate-fade-up">
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">المؤسسة</label>
            <select
              value={org ?? ""}
              onChange={(e) => setOrg(e.target.value || null)}
              className="w-full px-3 py-2.5 rounded-xl border border-soft-blue bg-white text-sm text-deep-navy outline-none focus:border-primary"
            >
              <option value="">كل المؤسسات</option>
              {organizations.map((o) => (
                <option key={o.id} value={o.id}>{o.shortName}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">المسار</label>
            <select
              value={track ?? ""}
              onChange={(e) => setTrack(e.target.value || null)}
              className="w-full px-3 py-2.5 rounded-xl border border-soft-blue bg-white text-sm text-deep-navy outline-none focus:border-primary"
            >
              <option value="">كل المسارات</option>
              {tracks.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">المستوى</label>
            <select
              value={level ?? ""}
              onChange={(e) => setLevel(e.target.value || null)}
              className="w-full px-3 py-2.5 rounded-xl border border-soft-blue bg-white text-sm text-deep-navy outline-none focus:border-primary"
            >
              <option value="">كل المستويات</option>
              {LEVELS.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {hasFilters && (
        <div className="flex items-center gap-2 mb-6">
          <span className="text-xs text-text-secondary">{filtered.length} نتيجة</span>
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:text-primary-dark"
          >
            <X size={12} />
            امسح الفلاتر
          </button>
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Search size={22} />}
          title="مش لاقيين برامج مطابقة للبحث"
          action={
            <button
              onClick={clearFilters}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary-dark transition-colors"
            >
              امسح الفلاتر
            </button>
          }
        />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((p) => (
            <ProgramCard key={p.id} program={p} />
          ))}
        </div>
      )}
    </div>
  );
}
