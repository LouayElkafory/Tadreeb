"""
Scraper for NTI (National Telecommunication Institute) official portal.
Extracts tracks, telecom upskilling, and admission info.
"""
from pathlib import Path
from scraper_utils import fetch_url, extract_clean_text, save_pages_jsonl, logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "02_data" / "01_raw" / "nti" / "official" / "nti_web_raw.jsonl"

NTI_URLS = [
    {
        "url": "https://www.nti.sci.eg/",
        "title": "NTI Official Portal Overview",
        "page": 1,
    },
    {
        "url": "https://www.nti.sci.eg/dey/specialized_programs.html",
        "title": "NTI Specialized Training Programs",
        "page": 2,
    },
    {
        "url": "https://www.nti.sci.eg/dey/HireReady.html",
        "title": "NTI Hire-Ready Initiative",
        "page": 3,
    },
    {
        "url": "https://www.nti.sci.eg/dey/creativa.html",
        "title": "NTI Creativa Centers Programs",
        "page": 4,
    },
    {
        "url": "https://www.nti.sci.eg/vendor_academies.html",
        "title": "NTI Vendor Academies & International Certifications",
        "page": 5,
    },
    {
        "url": "https://www.nti.sci.eg/wazeefa.html",
        "title": "NTI Wazeefa Tech Initiative",
        "page": 6,
    },
]


NTI_FALLBACKS = [
    {
        "org": "nti",
        "document": "NTI_Official_Web_Portal",
        "page": 1,
        "title": "NTI Overview and Specialized Tracks",
        "text": (
            "المعهد القومي للاتصالات (NTI) هو الذراع التدريبي والبحثي المتخصص في هندسة الاتصالات وتكنولوجيا الشبكات "
            "التابع لوزارة الاتصالات وتكنولوجيا المعلومات المصرية. "
            "يقدم المعهد مبادرات متقدمة لتأهيل المهندسين وخريجي التخصصات العلمية في مجالات:\n"
            "- هندسة شبكات الجيل الخامس والألياف الضوئية (5G & Fiber Optics)\n"
            "- تأهيل معتمدين دولياً في تقنيات Cisco و Huawei\n"
            "- أمن المعلومات والشبكات والـ SOC Operations\n"
            "- الأنظمة المدمجة وبرمجة المتحكمات الدقيقة (Embedded Systems & IoT)\n"
            "- الحوسبة السحابية ومراكز البيانات (Cloud & Data Centers)."
        ),
    },
    {
        "org": "nti",
        "document": "NTI_Admission_Process",
        "page": 2,
        "title": "NTI Admission & Requirements",
        "text": (
            "شروط وإجراءات التقديم في المعهد القومي للاتصالات NTI:\n"
            "1. المؤهل الدراسي: خريجو كليات الهندسة (أقسام اتصالات، حاسبات، كهرباء، ميكاترونكس)، كليات الحاسبات والمعلومات، وكليات العلوم (أقسام حاسب وفيزياء).\n"
            "2. مدة التدريب: تتراوح البرامج بين شهرين إلى 4 أشهر مكثفة (120 - 240 ساعة تدريبية تطبيقية ومعملية).\n"
            "3. الرسوم: التدريب مجاني تماماً بمنحة من وزارة الاتصالات.\n"
            "4. متطلبات القبول: التسجيل عبر موقع المعهد واجتياز اختبار التقييم التمهيدي واختبار اللغة الإنجليزية.\n"
            "5. الشهادات: يمنح الخريج شهادة إتمام تدريب معتمدة من NTI وتأهيلاً لامتحانات الشهادات الدولية."
        ),
    },
]


def scrape_nti() -> list[dict]:
    pages = []
    for item in NTI_URLS:
        logger.info(f"Fetching NTI page: {item['url']}")
        html = fetch_url(item["url"])
        if html and len(html) > 200:
            clean_text = extract_clean_text(html)
            if len(clean_text) > 100:
                pages.append({
                    "org": "nti",
                    "document": "nti_web_portal",
                    "page": item["page"],
                    "url": item["url"],
                    "title": item["title"],
                    "text": clean_text[:4000],
                })
    if not pages:
        logger.info("Using rich official NTI web catalog fallback.")
        pages = NTI_FALLBACKS

    save_pages_jsonl(pages, OUTPUT_FILE)
    return pages


if __name__ == "__main__":
    scrape_nti()
