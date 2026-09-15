import { GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";

export default function Logo({ light = false }: { light?: boolean }) {
  return (
    <Link to="/" className="flex items-center gap-2 shrink-0 group">
      <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-primary-dark text-white shadow-sm group-hover:scale-105 transition-transform">
        <GraduationCap size={20} strokeWidth={2.2} />
      </span>
      <span
        className={`text-xl font-bold tracking-tight ${light ? "text-white" : "text-deep-navy"}`}
      >
        تدريب
      </span>
    </Link>
  );
}
