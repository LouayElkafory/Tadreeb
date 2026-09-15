import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Mail, Lock, ArrowLeft, Info } from "lucide-react";
import Logo from "../components/Logo";

export default function Login() {
  const [notice, setNotice] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setNotice(true);
  };

  return (
    <div className="min-h-[calc(100vh-88px)] flex items-center justify-center px-5 py-16 bg-baby-blue/30">
      <div className="w-full max-w-md bg-white rounded-3xl border border-soft-blue shadow-[0_10px_40px_rgba(16,43,87,0.08)] p-8 sm:p-10">
        <div className="flex justify-center mb-6">
          <Logo />
        </div>
        <h1 className="text-xl font-extrabold text-deep-navy text-center mb-1.5">أهلاً بيك تاني</h1>
        <p className="text-sm text-text-secondary text-center mb-8">سجّل دخولك عشان تكمل تجربتك.</p>

        {notice && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-baby-blue text-primary-dark text-xs leading-relaxed mb-5">
            <Info size={15} className="shrink-0 mt-0.5" />
            دي واجهة تجريبية لتسجيل الدخول، وهتتفعل لاحقًا مع الربط بالخادم.
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">البريد الإلكتروني</label>
            <div className="relative">
              <Mail size={16} className="absolute top-1/2 -translate-y-1/2 start-3.5 text-text-secondary" />
              <input
                type="email"
                required
                placeholder="example@email.com"
                className="w-full ps-10 pe-4 py-3 rounded-xl border border-soft-blue bg-white focus:border-primary outline-none text-sm text-deep-navy"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">كلمة المرور</label>
            <div className="relative">
              <Lock size={16} className="absolute top-1/2 -translate-y-1/2 start-3.5 text-text-secondary" />
              <input
                type="password"
                required
                placeholder="••••••••"
                className="w-full ps-10 pe-4 py-3 rounded-xl border border-soft-blue bg-white focus:border-primary outline-none text-sm text-deep-navy"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="button" className="text-xs font-semibold text-primary hover:text-primary-dark">
              نسيت كلمة المرور؟
            </button>
          </div>
          <button
            type="submit"
            className="w-full py-3 rounded-xl text-sm font-bold text-white bg-primary hover:bg-primary-dark transition-colors shadow-sm"
          >
            تسجيل الدخول
          </button>
        </form>

        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-soft-blue" />
          <span className="text-xs text-text-secondary">أو</span>
          <div className="flex-1 h-px bg-soft-blue" />
        </div>

        <button className="w-full py-3 rounded-xl text-sm font-semibold text-deep-navy bg-baby-blue hover:bg-soft-blue transition-colors">
          المتابعة عبر Google
        </button>

        <p className="text-center text-xs text-text-secondary mt-6">
          لسه معملتش حساب؟{" "}
          <button className="text-primary font-semibold hover:underline">سجّل دلوقتي</button>
        </p>

        <Link
          to="/"
          className="flex items-center justify-center gap-1.5 text-xs font-medium text-text-secondary hover:text-primary mt-6"
        >
          <ArrowLeft size={13} className="rotate-180 rtl:rotate-0" />
          العودة للرئيسية
        </Link>
      </div>
    </div>
  );
}
