import { MessageCircleQuestion, Search, Sparkles, Link2 } from 'lucide-react'
import { useLanguage } from '@/hooks/useLanguage'

const steps = [
  {
    icon: MessageCircleQuestion,
    titleKey: 'home.trustStep.1.title',
    textKey: 'home.trustStep.1.desc',
  },
  {
    icon: Search,
    titleKey: 'home.trustStep.2.title',
    textKey: 'home.trustStep.2.desc',
  },
  {
    icon: Sparkles,
    titleKey: 'home.trustStep.3.title',
    textKey: 'home.trustStep.3.desc',
  },
  {
    icon: Link2,
    titleKey: 'home.trustStep.4.title',
    textKey: 'home.trustStep.4.desc',
  },
]

export default function TrustSection() {
  const { t } = useLanguage()

  return (
    <section id="sources" className="relative bg-[var(--color-baby-blue)] px-5 py-20 sm:py-28">
      <div className="mx-auto max-w-5xl text-center">
        <h2 className="text-balance text-2xl font-extrabold text-[var(--color-deep-navy)] sm:text-3xl">
          {t("home.trustTitle")}
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-balance text-[15px] leading-relaxed text-[var(--color-text-secondary)] sm:text-base">
          {t("home.trustBody")}
        </p>

        <div className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <div
              key={step.titleKey}
              className="animate-fade-up flex flex-col items-center text-center"
              style={{ animationDelay: `${i * 90}ms` }}
            >
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-[var(--color-primary)] shadow-[var(--shadow-soft)]">
                <step.icon size={24} strokeWidth={1.75} />
              </div>
              <h3 className="text-[15px] font-bold text-[var(--color-deep-navy)]">{t(step.titleKey)}</h3>
              <p className="mt-1.5 max-w-[220px] text-sm leading-relaxed text-[var(--color-text-secondary)]">
                {t(step.textKey)}
              </p>
              {i < steps.length - 1 && (
                <div
                  className="mt-6 hidden h-px w-full bg-gradient-to-r from-[var(--color-primary)]/20 to-transparent lg:block"
                  aria-hidden="true"
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
