import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, X, Globe } from "lucide-react";
import Logo from "./Logo";
import { useLanguage } from "../hooks/useLanguage";

const NAV_LINKS = [
  { to: "/", labelKey: "nav.home" },
  { to: "/sources", labelKey: "nav.sources" },
  { to: "/assistant", labelKey: "nav.assistant" },
  { to: "/organizations", labelKey: "nav.organizations" },
  { to: "/programs", labelKey: "nav.programs" },
];

export default function Navbar({ transparent = false }: { transparent?: boolean }) {
  const [open, setOpen] = useState(false);
  const { t, toggleLanguage } = useLanguage();

  return (
    <>
      <header className="sticky top-0 z-50 px-3 pt-3 sm:px-4 sm:pt-4">
        <nav
          className={`mx-auto flex max-w-6xl items-center justify-between rounded-2xl border px-3 py-2 sm:px-5 sm:py-2.5 transition-colors ${
            transparent
              ? "bg-white/70 backdrop-blur-md border-white/60 shadow-[0_8px_30px_rgba(16,43,87,0.08)]"
              : "bg-white/90 backdrop-blur-md border-soft-blue shadow-[0_8px_30px_rgba(16,43,87,0.06)]"
          }`}
        >
          <Logo />

          <div className="hidden lg:flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `relative px-3.5 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? "text-primary after:absolute after:bottom-0 after:start-3.5 after:end-3.5 after:h-0.5 after:bg-primary after:rounded-full"
                      : "text-text-secondary hover:text-primary hover:bg-baby-blue"
                  }`
                }
              >
                {t(link.labelKey)}
              </NavLink>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleLanguage}
              className="hidden sm:flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-text-secondary hover:text-primary rounded-lg hover:bg-baby-blue transition-colors"
              aria-label={t("nav.switchAria")}
            >
              <Globe size={16} />
              {t("nav.switchTo")}
            </button>
            <Link
              to="/login"
              className="hidden sm:inline-flex items-center px-5 py-2 text-sm font-semibold text-white bg-primary hover:bg-primary-dark rounded-full transition-colors shadow-sm"
            >
              {t("nav.login")}
            </Link>
            <button
              className="lg:hidden p-2 rounded-lg text-deep-navy hover:bg-baby-blue transition-colors"
              onClick={() => setOpen(true)}
              aria-label={t("nav.openMenu")}
            >
              <Menu size={22} />
            </button>
          </div>
        </nav>
      </header>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-[60] lg:hidden">
          <div
            className="absolute inset-0 bg-deep-navy/40 backdrop-blur-sm animate-fade-in"
            onClick={() => setOpen(false)}
          />
          <div className="absolute top-0 start-0 h-full w-[82%] max-w-xs bg-white shadow-2xl p-5 flex flex-col animate-fade-up">
            <div className="flex items-center justify-between mb-8">
              <Logo />
              <button
                onClick={() => setOpen(false)}
                className="p-2 rounded-lg hover:bg-baby-blue text-deep-navy"
                aria-label={t("nav.closeMenu")}
              >
                <X size={22} />
              </button>
            </div>
            <div className="flex flex-col gap-1">
              {NAV_LINKS.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `px-4 py-3 rounded-xl text-base font-medium transition-colors ${
                      isActive ? "bg-baby-blue text-primary" : "text-deep-navy hover:bg-baby-blue"
                    }`
                  }
                >
                  {t(link.labelKey)}
                </NavLink>
              ))}
            </div>
            <div className="mt-auto flex flex-col gap-2 pt-6 border-t border-soft-blue">
              <button
                onClick={toggleLanguage}
                className="flex items-center gap-2 px-4 py-3 rounded-xl text-base font-medium text-deep-navy hover:bg-baby-blue"
              >
                <Globe size={18} />
                {t("nav.switchTo")}
              </button>
              <Link
                to="/login"
                onClick={() => setOpen(false)}
                className="text-center px-4 py-3 rounded-xl text-base font-semibold text-white bg-primary"
              >
                {t("nav.login")}
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
