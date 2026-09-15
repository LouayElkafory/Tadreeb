import { Link } from "react-router-dom";
import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="border-t border-soft-blue bg-baby-blue/40">
      <div className="max-w-6xl mx-auto px-5 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1">
            <Logo />
            <p className="mt-4 text-sm text-text-secondary leading-relaxed max-w-xs">
              مساعد ذكي بيساعدك تكتشف فرص التدريب التقني في مصر من مصادر موثوقة.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-deep-navy mb-3">استكشف</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><Link to="/programs" className="hover:text-primary transition-colors">البرامج</Link></li>
              <li><Link to="/organizations" className="hover:text-primary transition-colors">المؤسسات</Link></li>
              <li><Link to="/sources" className="hover:text-primary transition-colors">المصادر</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-deep-navy mb-3">المساعد</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><Link to="/chat" className="hover:text-primary transition-colors">ابدأ المحادثة</Link></li>
              <li><Link to="/assistant" className="hover:text-primary transition-colors">عن المساعد الذكي</Link></li>
              <li><Link to="/login" className="hover:text-primary transition-colors">تسجيل الدخول</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-deep-navy mb-3">تدريب</h4>
            <p className="text-sm text-text-secondary leading-relaxed">
              منصة مستقلة لإتاحة معلومات التدريب التقني في مكان واحد.
            </p>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-soft-blue text-xs text-text-secondary flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>© {new Date().getFullYear()} تدريب. جميع الحقوق محفوظة.</span>
          <span>صُنع بعناية لدعم رحلتك التقنية.</span>
        </div>
      </div>
    </footer>
  );
}
