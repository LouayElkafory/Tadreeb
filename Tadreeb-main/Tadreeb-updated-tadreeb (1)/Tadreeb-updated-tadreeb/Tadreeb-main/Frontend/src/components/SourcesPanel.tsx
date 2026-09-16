import { X, BookOpen } from "lucide-react";
import SourceCard from "./SourceCard";
import EmptyState from "./EmptyState";
import type { Source } from "../types";
import { useLanguage } from "../hooks/useLanguage";

interface SourcesPanelProps {
  sources: Source[];
  onClose?: () => void;
  isLoading?: boolean;
}

export default function SourcesPanel({ sources, onClose, isLoading }: SourcesPanelProps) {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex items-center justify-between px-4 py-4 border-b border-soft-blue shrink-0">
        <div>
          <h2 className="text-sm font-bold text-deep-navy">{t("chat.sourcesTitle")}</h2>
          <p className="text-xs text-text-secondary mt-0.5">{t("sources.available", { count: sources.length })}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-text-secondary hover:text-deep-navy hover:bg-baby-blue transition-colors"
            aria-label={t("sources.close")}
          >
            <X size={18} />
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 rounded-2xl bg-baby-blue/60 animate-pulse" />
            ))}
          </div>
        ) : sources.length === 0 ? (
          <EmptyState
            icon={<BookOpen size={22} />}
            title={t("sources.panelEmptyTitle")}
            description={t("sources.panelEmptyBody")}
          />
        ) : (
          <div className="space-y-3">
            {sources.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
