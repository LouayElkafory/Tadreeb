import { Link } from "react-router-dom";
import { Home, MessageCircle, Compass } from "lucide-react";
import Logo from "../components/Logo";
import { useLanguage } from "../hooks/useLanguage";

export default function NotFound() {
  const { t } = useLanguage();

  return (
    <div className="min-h-[calc(100vh-88px)] flex items-center justify-center px-5 py-16">
      <div className="text-center max-w-md">
        <div className="flex justify-center mb-8">
          <Logo />
        </div>
        <div className="w-20 h-20 rounded-3xl bg-baby-blue text-primary flex items-center justify-center mx-auto mb-6">
          <Compass size={32} />
        </div>
        <span className="text-7xl font-extrabold text-soft-blue block mb-2">404</span>
        <h1 className="text-2xl font-extrabold text-deep-navy mb-3">{t("notFound.title")}</h1>
        <p className="text-text-secondary text-base leading-relaxed mb-10">
          {t("notFound.body")}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-bold text-white bg-primary hover:bg-primary-dark shadow-sm transition-colors"
          >
            <Home size={16} />
            {t("common.backHome")}
          </Link>
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-bold text-deep-navy bg-baby-blue hover:bg-soft-blue transition-colors"
          >
            <MessageCircle size={16} />
            {t("notFound.openAssistant")}
          </Link>
        </div>
      </div>
    </div>
  );
}
