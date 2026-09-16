import { Sun, Moon } from "lucide-react";
import { useTheme } from "../hooks/useTheme";
import { useLanguage } from "../hooks/useLanguage";

export default function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const { t } = useLanguage();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={t(isDark ? "theme.switchToLight" : "theme.switchToDark")}
      title={t(isDark ? "theme.switchToLight" : "theme.switchToDark")}
      className={`inline-flex items-center justify-center rounded-full text-text-secondary transition-all duration-300 hover:text-primary hover:bg-baby-blue hover:rotate-12 ${className}`}
    >
      {isDark ? <Moon size={17} /> : <Sun size={17} />}
    </button>
  );
}
