export default function LoadingIndicator({ label = "المساعد بيفكر..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 animate-fade-in">
      <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl bg-white border border-soft-blue shadow-sm">
        <span className="w-2 h-2 rounded-full bg-primary dot-pulse" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 rounded-full bg-primary dot-pulse" style={{ animationDelay: "160ms" }} />
        <span className="w-2 h-2 rounded-full bg-primary dot-pulse" style={{ animationDelay: "320ms" }} />
      </div>
      <span className="text-sm text-text-secondary">{label}</span>
    </div>
  );
}
