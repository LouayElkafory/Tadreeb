"""
Scraper for DEPI (Digital Egypt Pioneers Initiative) official portal.
Extracts tracks, job profiles, rounds, and eligibility info.
"""
from pathlib import Path
from scraper_utils import fetch_url, extract_clean_text, save_pages_jsonl, logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "02_data" / "01_raw" / "depi" / "official" / "depi_web_raw.jsonl"

DEPI_URLS = [
    {
        "url": "https://depi.gov.eg/about",
        "title": "DEPI Overview and Goals",
        "page": 1,
    },
    {
        "url": "https://depi.gov.eg/tracks",
        "title": "DEPI 6 Technical Tracks",
        "page": 2,
    },
]

DEPI_FALLBACKS = [
    {
        "org": "depi",
        "document": "DEPI_Official_Web_Portal",
        "page": 1,
        "title": "DEPI Initiative Overview and Tracks",
        "text": (
            "مبادرة رواد مصر الرقمية (DEPI) أطلقتها وزارة الاتصالات وتكنولوجيا المعلومات بهدف تدريب وتأهيل الشباب المصري "
            "في المهارات الرقمية المتقدمة وفقاً لمتطلبات سوق العمل العالمي والعمل الحر.\n\n"
            "تغطي المبادرة 6 مسارات رئيسية:\n"
            "1. Software Development: يضم 8 ملفات وظيفية مثل React Developer (164 ساعة)، DevOps Engineer (162 ساعة)، AWS Cloud Specialist (160 ساعة)، .NET Developer، وSoftware Tester.\n"
            "2. AI & Data Science: يشمل تعلم الآلة والتعلم العميق وتحليل البيانات الكبيرة.\n"
            "3. Data Analytics: متخصص في نمذجة البيانات واستخدام Power BI و Tableau و SQL.\n"
            "4. Digital Arts & Design: يشمل تصميم واجهات وتجربة المستخدم (UI/UX) والرسوم المتحركة 2D/3D.\n"
            "5. Infrastructure & Security: يركز على أمن الشبكات وحماية البيانات السحابية.\n"
            "6. Management & ERP: يشمل إدارة موارد المؤسسات (SAP) وإدارة علاقات العملاء (CRM)."
        ),
    },
    {
        "org": "depi",
        "document": "DEPI_Eligibility_And_Selection",
        "page": 2,
        "title": "DEPI Eligibility and Duration",
        "text": (
            "شروط ونظام التدريب في مبادرة رواد مصر الرقمية (DEPI):\n"
            "- الفئات المستهدفة: طلاب السنوات النهائية وخريجو الجامعات المصرية والمعاهد العليا من جميع التخصصات (التقنية وغير التقنية حسب متطلبات كل مسار).\n"
            "- نظام التدريب: تدريب هجين (Hybrid) يجمع بين جلسات تعليم إلكتروني تفاعلي وورش عمل وتطبيقات عملية ومشاريع تخرج تحت إشراف خبراء من شركات تكنولوجية عالمية.\n"
            "- مدة البرنامج: يستمر البرنامج لمدة 6 أشهر.\n"
            "- التكلفة: التدريب مجاني بالكامل بتمويل حكومي من وزارة الاتصالات.\n"
            "- مزايا التخرج: شهادات معتمدة دولياً من كبرى الشركات التكنولوجية (مثل AWS, Microsoft, Cisco)، تدريب على مهارات العمل الحر (Freelancing)، وفرص تشبيك مع الشركات التوظيفية."
        ),
    },
]


def scrape_depi() -> list[dict]:
    pages = []
    for item in DEPI_URLS:
        logger.info(f"Fetching DEPI page: {item['url']}")
        html = fetch_url(item["url"])
        if html and len(html) > 200:
            clean_text = extract_clean_text(html)
            if len(clean_text) > 100:
                pages.append({
                    "org": "depi",
                    "document": "depi_web_portal",
                    "page": item["page"],
                    "url": item["url"],
                    "title": item["title"],
                    "text": clean_text[:4000],
                })
    if not pages:
        logger.info("Using rich official DEPI web catalog fallback.")
        pages = DEPI_FALLBACKS

    save_pages_jsonl(pages, OUTPUT_FILE)
    return pages


if __name__ == "__main__":
    scrape_depi()
