import OrganizationCard from "../components/OrganizationCard";
import { organizations } from "../data/organizations";

export default function Organizations() {
  return (
    <div className="max-w-6xl mx-auto px-5 py-16 sm:py-20">
      <div className="text-center max-w-xl mx-auto mb-14">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-deep-navy mb-4">اكتشف المؤسسات التدريبية</h1>
        <p className="text-text-secondary text-base leading-relaxed">
          اعرف أكتر عن الجهات اللي بتقدم فرص تدريب تقني.
        </p>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {organizations.map((org) => (
          <OrganizationCard key={org.id} org={org} />
        ))}
      </div>
    </div>
  );
}
