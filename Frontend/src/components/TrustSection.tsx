import { MessageCircleQuestion, Search, Sparkles, Link2 } from 'lucide-react'

const steps = [
  {
    icon: MessageCircleQuestion,
    title: 'اسأل براحتك',
    text: 'اكتب سؤالك بالعامية المصرية أو بأي طريقة تريحك.',
  },
  {
    icon: Search,
    title: 'بندور في مصادر موثوقة',
    text: 'المساعد بيراجع معلومات ITI و NTI و DEPI و MCIT وغيرها.',
  },
  {
    icon: Sparkles,
    title: 'بنجهز إجابة واضحة',
    text: 'إجابة مبنية فعليًا على المصادر، مش تخمين.',
  },
  {
    icon: Link2,
    title: 'بنوريك المصدر',
    text: 'كل إجابة بتيجي معاها المصادر اللي اتبنت عليها.',
  },
]

export default function TrustSection() {
  return (
    <section id="sources" className="relative bg-[var(--color-baby-blue)] px-5 py-20 sm:py-28">
      <div className="mx-auto max-w-5xl text-center">
        <h2 className="text-balance text-2xl font-extrabold text-[var(--color-deep-navy)] sm:text-3xl">
          اسأل براحتك. وإحنا نجيبلك الإجابة من المصادر.
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-balance text-[15px] leading-relaxed text-[var(--color-text-secondary)] sm:text-base">
          معلومات التدريب، البرامج، وشروط التقديم في مكان واحد.
        </p>

        <div className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <div
              key={step.title}
              className="animate-fade-up flex flex-col items-center text-center"
              style={{ animationDelay: `${i * 90}ms` }}
            >
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-[var(--color-primary)] shadow-[var(--shadow-soft)]">
                <step.icon size={24} strokeWidth={1.75} />
              </div>
              <h3 className="text-[15px] font-bold text-[var(--color-deep-navy)]">{step.title}</h3>
              <p className="mt-1.5 max-w-[220px] text-sm leading-relaxed text-[var(--color-text-secondary)]">
                {step.text}
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
