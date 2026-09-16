import OrganizationCard from "../components/OrganizationCard";
import { organizations } from "../data/organizations";
import { useLanguage } from "../hooks/useLanguage";

export default function Organizations() {
  const { t } = useLanguage();

  return (
    <div className="max-w-6xl mx-auto px-5 py-16 sm:py-20">
      <div className="animate-fade-up text-center max-w-xl mx-auto mb-14">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-deep-navy mb-4">{t("organizations.title")}</h1>
        <p className="text-text-secondary text-base leading-relaxed">
          {t("organizations.body")}
        </p>
      </div>
      <div className="animate-fade-up grid sm:grid-cols-2 lg:grid-cols-4 gap-5 [animation-delay:80ms]">
        {organizations.map((org) => (
          <OrganizationCard key={org.id} org={org} />
        ))}
      </div>
    </div>
  );
}
