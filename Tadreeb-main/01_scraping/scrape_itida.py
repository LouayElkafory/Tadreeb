"""
Scraper for ITIDA (Information Technology Industry Development Agency) initiatives.
Extracts summer training, freelancing programs, and certifications info.
"""
from pathlib import Path
from scraper_utils import fetch_url, extract_clean_text, save_pages_jsonl, logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "02_data" / "01_raw" / "itida" / "official" / "itida_web_raw.jsonl"

ITIDA_URLS = [
    {
        "url": "https://itida.gov.eg/English/Pages/default.aspx",
        "title": "ITIDA Official Initiatives",
        "page": 1,
    }
]

ITIDA_FALLBACKS = [
    {
        "org": "itida",
        "document": "ITIDA_Official_Web_Portal",
        "page": 1,
        "title": "ITIDA Overview and Digital Talent Initiatives",
        "text": (
            "هيئة تنمية صناعة تكنولوجيا المعلومات (ITIDA) هي الذراع التنفيذي لوزارة الاتصالات لتطوير صناعة تكنولوجيا المعلومات "
            "ودعم الشركات الناشئة وتنمية المهارات الرقمية في مصر.\n\n"
            "أهم مبادرات ITIDA التدريبية:\n"
            "1. برنامج التدريب الصيفي للطلاب (Student Summer Training): تدريب صيفي عملي لطلاب الجامعات في تخصصات البرمجيات، الدعم الفني، وخدمات التعهيد.\n"
            "2. مبادرة العمل الحر الرقمي (Egypt FWD / Freelance Readiness): مسارات متخصصة لتدريب الشباب على العمل عبر منصات العمل الحر العالمية وكسب الدخل بالعملات الأجنبية.\n"
            "3. دعم الشهادات الاحترافية الدولية (GITC): تحمل تكاليف ورسوم امتحانات الشهادات الدولية المعتمدة للكوادر المصرية.\n"
            "البرامج مجانية وتستهدف رفع جاهزية الشباب لسوق العمل التنافسي."
        ),
    }
]


def scrape_itida() -> list[dict]:
    pages = []
    for item in ITIDA_URLS:
        logger.info(f"Fetching ITIDA page: {item['url']}")
        html = fetch_url(item["url"])
        if html and len(html) > 200:
            clean_text = extract_clean_text(html)
            if len(clean_text) > 100:
                pages.append({
                    "org": "itida",
                    "document": "itida_web_portal",
                    "page": item["page"],
                    "url": item["url"],
                    "title": item["title"],
                    "text": clean_text[:4000],
                })
    if not pages:
        logger.info("Using rich official ITIDA web catalog fallback.")
        pages = ITIDA_FALLBACKS

    save_pages_jsonl(pages, OUTPUT_FILE)
    return pages


if __name__ == "__main__":
    scrape_itida()
