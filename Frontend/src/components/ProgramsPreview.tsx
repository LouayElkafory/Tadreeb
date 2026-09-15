import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import ProgramCard from './ProgramCard'
import { programs } from '@/data/programs'

export default function ProgramsPreview() {
  const preview = programs.slice(0, 4)

  return (
    <section id="institutions" className="bg-white px-5 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold text-[var(--color-deep-navy)] sm:text-3xl">
              برامج تدريبية مختارة
            </h2>
            <p className="mt-2 max-w-md text-[15px] leading-relaxed text-[var(--color-text-secondary)]">
              نماذج من مسارات ITI و NTI و DEPI و MCIT — اسأل المساعد الذكي لتفاصيل أكتر.
            </p>
          </div>
          <Link
            to="/programs"
            className="flex items-center gap-1.5 rounded-xl border border-[var(--color-border-soft)] px-4 py-2.5 text-sm font-semibold text-[var(--color-primary-dark)] transition-colors hover:bg-[var(--color-baby-blue)]"
          >
            كل البرامج
            <ArrowLeft size={15} />
          </Link>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {preview.map((program, i) => (
            <div key={program.id} className="animate-fade-up" style={{ animationDelay: `${i * 70}ms` }}>
              <ProgramCard program={program} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
