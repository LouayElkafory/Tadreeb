import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import Navbar from './Navbar'
import ChatInput from './ChatInput'
import SuggestedQuestions from './SuggestedQuestions'
import { useLanguage } from '@/context/LanguageContext'

const suggestions = [
  'إيه شروط التقديم في ITI؟',
  'أنا خريج تجارة، إيه البرامج المناسبة ليا؟',
  'هل التدريب مجاني؟',
  'إيه أفضل مسار للـ AI؟',
]

export default function Hero() {
  const [imgFailed, setImgFailed] = useState(false)
  const navigate = useNavigate()
  const { t } = useLanguage()

  const goToChat = (message?: string) => {
    if (message) {
      sessionStorage.setItem('tadreeb.pendingMessage', message)
    }
    navigate('/chat')
  }

  return (
    <section className="relative isolate min-h-[100svh] w-full overflow-hidden bg-[var(--color-deep-navy)]">
      {/* Cinematic background */}
      <div className="absolute inset-0 -z-10">
        {!imgFailed ? (
          <img
            src="/main.png"
            alt=""
            onError={() => setImgFailed(true)}
            className="h-full w-full object-cover object-center"
          />
        ) : (
          <FallbackBackdrop />
        )}
        {/* Gentle readability overlay — kept light to preserve the artwork */}
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-deep-navy)]/55 via-transparent to-[var(--color-deep-navy)]/70" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[var(--color-baby-blue)] to-transparent" />
      </div>

      <Navbar />

      <div className="relative z-10 mx-auto flex min-h-[100svh] w-full max-w-3xl flex-col items-center justify-center px-5 pb-16 pt-32 text-center sm:pt-40">
        <span className="animate-fade-up mb-5 inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-4 py-1.5 text-sm font-medium text-white backdrop-blur-md">
          <ShieldCheck size={15} className="text-[var(--color-sky-blue)]" />
          {t('hero_trust')}
        </span>

        <h1 className="animate-fade-up text-balance text-3xl font-extrabold leading-[1.35] text-white [animation-delay:80ms] sm:text-4xl md:text-5xl">
          {t('hero_headline')}
        </h1>

        <p className="animate-fade-up mt-4 text-balance text-lg font-medium text-[var(--color-sky-blue)] [animation-delay:140ms] sm:text-xl">
          {t('hero_subheadline')}
        </p>

        <p className="animate-fade-up mt-3 max-w-xl text-balance text-[15px] leading-relaxed text-white/80 [animation-delay:200ms] sm:text-base">
          {t('hero_support')}
        </p>

        <div className="animate-fade-up mt-8 w-full max-w-xl [animation-delay:260ms]">
          <ChatInput
            size="lg"
            autoFocus={false}
            onSend={(message) => goToChat(message)}
            placeholder={t('hero_input_placeholder')}
          />
        </div>

        <div className="animate-fade-up mt-5 w-full max-w-2xl [animation-delay:320ms]">
          <SuggestedQuestions
            questions={suggestions}
            onSelect={(q) => goToChat(q)}
          />
        </div>

        <div className="animate-fade-up mt-9 flex flex-wrap items-center justify-center gap-3 [animation-delay:380ms]">
          <button
            onClick={() => goToChat()}
            className="rounded-2xl bg-white px-6 py-3 text-[15px] font-bold text-[var(--color-primary-dark)] shadow-[0_15px_40px_-12px_rgba(255,255,255,0.5)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_20px_50px_-12px_rgba(255,255,255,0.6)]"
          >
            {t('hero_cta_primary')}
          </button>
          <button
            onClick={() => navigate('/programs')}
            className="rounded-2xl border border-white/30 bg-white/10 px-6 py-3 text-[15px] font-semibold text-white backdrop-blur-md transition-all duration-300 hover:-translate-y-0.5 hover:bg-white/20"
          >
            {t('hero_cta_secondary')}
          </button>
        </div>
      </div>
    </section>
  )
}

/**
 * Fallback cinematic backdrop used only if /main.png fails to load.
 * Drop the real artwork at public/main.png to have it take over automatically.
 */
function FallbackBackdrop() {
  return (
    <div className="relative h-full w-full overflow-hidden bg-gradient-to-b from-[#0a3d91] via-[#155bc4] to-[#eaf5ff]">
      <div className="absolute left-1/2 top-[38%] h-[340px] w-[340px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-br from-[#bfe6ff] via-[#3fd0e0] to-[#1677e8] opacity-90 blur-[2px] animate-soft-float sm:h-[440px] sm:w-[440px]" />
      <div className="absolute left-1/2 top-[38%] h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full shadow-[0_0_180px_80px_rgba(140,203,255,0.35)] sm:h-[540px] sm:w-[540px]" />
      <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-white/50 to-transparent" />
      <svg
        className="absolute bottom-0 left-0 w-full opacity-40"
        viewBox="0 0 1200 200"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d="M0 200 L0 120 L60 90 L100 130 L160 70 L220 130 L280 100 L340 140 L420 60 L480 130 L560 90 L640 150 L720 100 L800 140 L880 80 L960 140 L1040 110 L1120 150 L1200 100 L1200 200 Z"
          fill="#0d47a1"
        />
      </svg>
      <div className="absolute inset-0 opacity-30 [background:radial-gradient(circle_at_20%_20%,white,transparent_35%),radial-gradient(circle_at_75%_15%,white,transparent_30%)]" />
    </div>
  )
}
