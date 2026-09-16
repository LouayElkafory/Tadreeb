import { useLanguage } from "../hooks/useLanguage";

export default function LoadingIndicator({ label }: { label?: string }) {
  const { t } = useLanguage();

  return (
    <div className="flex items-center gap-3 animate-fade-in">
      <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl bg-white border border-soft-blue shadow-sm">
        <span className="w-2 h-2 rounded-full bg-primary dot-pulse" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 rounded-full bg-primary dot-pulse" style={{ animationDelay: "160ms" }} />
        <span className="w-2 h-2 rounded-full bg-primary dot-pulse" style={{ animationDelay: "320ms" }} />
      </div>
      <span className="text-sm text-text-secondary">{label ?? t("chat.thinking")}</span>
    </div>
  );
}
