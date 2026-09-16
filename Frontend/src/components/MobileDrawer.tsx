import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";
import { useLanguage } from "../hooks/useLanguage";

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  side?: "start" | "end";
}

export default function MobileDrawer({ open, onClose, title, children, side = "start" }: MobileDrawerProps) {
  const { t } = useLanguage();

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  const sideClass = side === "start" ? "start-0" : "end-0";

  return (
    <div className="fixed inset-0 z-[70]" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-deep-navy/40 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div
        className={`absolute top-0 ${sideClass} h-full w-[85%] max-w-sm bg-white shadow-2xl flex flex-col animate-fade-up`}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-soft-blue shrink-0">
          <h2 className="text-base font-bold text-deep-navy">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-baby-blue text-deep-navy"
            aria-label={t("nav.closeMenu")}
          >
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
