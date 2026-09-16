import { Link } from "react-router-dom";
import Logo from "./Logo";
import { useLanguage } from "../hooks/useLanguage";

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="border-t border-soft-blue bg-baby-blue/40">
      <div className="max-w-6xl mx-auto px-5 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1">
            <Logo />
            <p className="mt-4 text-sm text-text-secondary leading-relaxed max-w-xs">
              {t("footer.description")}
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-deep-navy mb-3">{t("footer.explore")}</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><Link to="/programs" className="hover:text-primary transition-colors">{t("nav.programs")}</Link></li>
              <li><Link to="/organizations" className="hover:text-primary transition-colors">{t("nav.organizations")}</Link></li>
              <li><Link to="/sources" className="hover:text-primary transition-colors">{t("nav.sources")}</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-deep-navy mb-3">{t("footer.assistant")}</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><Link to="/chat" className="hover:text-primary transition-colors">{t("common.startChat")}</Link></li>
              <li><Link to="/assistant" className="hover:text-primary transition-colors">{t("footer.aboutAssistant")}</Link></li>
              <li><Link to="/login" className="hover:text-primary transition-colors">{t("footer.signIn")}</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-deep-navy mb-3">{t("brand.name")}</h4>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t("footer.about")}
            </p>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-soft-blue text-xs text-text-secondary flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>{t("footer.rights", { year: new Date().getFullYear() })}</span>
          <span>{t("footer.made")}</span>
        </div>
      </div>
    </footer>
  );
}
