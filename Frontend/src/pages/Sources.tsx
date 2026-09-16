import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import SourceCard from "../components/SourceCard";
import EmptyState from "../components/EmptyState";
import { sources } from "../data/sources";
import type { SourceType } from "../types";
import { useLanguage } from "../hooks/useLanguage";

const TYPES: { value: SourceType; labelKey: string }[] = [
  { value: "official", labelKey: "source.official" },
  { value: "government", labelKey: "source.government" },
  { value: "document", labelKey: "source.document" },
  { value: "community", labelKey: "source.community" },
];

export default function Sources() {
  const [search, setSearch] = useState("");
  const [org, setOrg] = useState<string | null>(null);
  const [type, setType] = useState<SourceType | null>(null);
  const { localize, t } = useLanguage();

  const organizations = useMemo(
    () => Array.from(new Map(sources.map((s) => [s.organization.en, s.organization])).values()),
    []
  );

  const filtered = useMemo(() => {
    const normalizedSearch = search.toLowerCase();
    return sources.filter((s) => {
      const matchesSearch =
        !search ||
        localize(s.title).toLowerCase().includes(normalizedSearch) ||
        (s.description ? localize(s.description).toLowerCase().includes(normalizedSearch) : false);
      const matchesOrg = !org || s.organization.en === org;
      const matchesType = !type || s.type === type;
      return matchesSearch && matchesOrg && matchesType;
    });
  }, [localize, search, org, type]);

  const clear = () => {
    setSearch("");
    setOrg(null);
    setType(null);
  };

  return (
    <div className="max-w-6xl mx-auto px-5 py-14 sm:py-16">
      <div className="text-center max-w-xl mx-auto mb-10">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-deep-navy mb-4">{t("sources.title")}</h1>
        <p className="text-text-secondary text-base leading-relaxed">
          {t("sources.body")}
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={17} className="absolute top-1/2 -translate-y-1/2 start-4 text-text-secondary" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("sources.search")}
            className="w-full ps-11 pe-4 py-3 rounded-2xl border border-soft-blue bg-white focus:border-primary outline-none text-sm text-deep-navy placeholder:text-text-secondary/70"
          />
        </div>
        <select
          value={org ?? ""}
          onChange={(e) => setOrg(e.target.value || null)}
          className="px-4 py-3 rounded-2xl border border-soft-blue bg-white text-sm text-deep-navy outline-none focus:border-primary"
        >
          <option value="">{t("common.allOrganizations")}</option>
          {organizations.map((o) => (
            <option key={o.en} value={o.en}>{localize(o)}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap gap-2 mb-8">
        {TYPES.map((sourceType) => (
          <button
            key={sourceType.value}
            onClick={() => setType(type === sourceType.value ? null : sourceType.value)}
            className={`px-4 py-2 rounded-full text-sm font-semibold border transition-colors ${
              type === sourceType.value
                ? "bg-primary text-white border-primary"
                : "bg-white text-deep-navy border-soft-blue hover:border-primary"
            }`}
          >
            {t(sourceType.labelKey)}
          </button>
        ))}
        {(search || org || type) && (
          <button
            onClick={clear}
            className="inline-flex items-center gap-1 px-4 py-2 rounded-full text-sm font-semibold text-primary hover:text-primary-dark"
          >
            <X size={14} />
            {t("common.clearSearch")}
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Search size={22} />}
          title={t("sources.emptyTitle")}
          action={
            <button
              onClick={clear}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary-dark transition-colors"
            >
              {t("common.clearSearch")}
            </button>
          }
        />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((s) => (
            <SourceCard key={s.id} source={s} />
          ))}
        </div>
      )}
    </div>
  );
}
