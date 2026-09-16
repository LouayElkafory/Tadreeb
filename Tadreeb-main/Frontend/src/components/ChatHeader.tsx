import { PanelRight, PanelLeft, Plus, ShieldCheck } from "lucide-react";
import Logo from "./Logo";
import { useLanguage } from "../hooks/useLanguage";

interface ChatHeaderProps {
  onOpenHistory: () => void;
  onToggleSources: () => void;
  onNewChat: () => void;
  sourcesOpen: boolean;
}

export default function ChatHeader({ onOpenHistory, onToggleSources, onNewChat, sourcesOpen }: ChatHeaderProps) {
  const { t } = useLanguage();

  return (
    <header className="flex items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4 border-b border-soft-blue bg-white/80 backdrop-blur-md shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenHistory}
          className="lg:hidden p-2 rounded-lg text-deep-navy hover:bg-baby-blue transition-colors shrink-0"
          aria-label={t("chat.historyTitle")}
        >
          <PanelLeft size={20} />
        </button>
        <div className="hidden sm:block shrink-0">
          <Logo />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-sm sm:text-base font-bold text-deep-navy truncate">{t("chat.headerTitle")}</h1>
            <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {t("chat.online")}
            </span>
          </div>
          <p className="hidden sm:flex items-center gap-1 text-[11px] text-text-secondary">
            <ShieldCheck size={11} />
            {t("chat.trust")}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1.5 shrink-0">
        <button
          onClick={onNewChat}
          className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold text-primary bg-baby-blue hover:bg-soft-blue transition-colors"
        >
          <Plus size={16} />
          {t("chat.new")}
        </button>
        <button
          onClick={onNewChat}
          className="sm:hidden p-2 rounded-lg text-deep-navy hover:bg-baby-blue transition-colors"
          aria-label={t("chat.new")}
        >
          <Plus size={20} />
        </button>
        <button
          onClick={onToggleSources}
          className={`p-2 rounded-lg transition-colors ${
            sourcesOpen ? "text-primary bg-baby-blue" : "text-deep-navy hover:bg-baby-blue"
          }`}
          aria-label={t("chat.sourcesTitle")}
          title={t("chat.sourcesTitle")}
        >
          <PanelRight size={20} />
        </button>
      </div>
    </header>
  );
}
