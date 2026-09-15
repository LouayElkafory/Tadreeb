# ترتيب العمل على الملفات (File Order Guide)
## نسخة المسارين المتوازيين: RAG + Fine-tuning

---

## المرحلة 0 — قبل أي كود
```
requirements.txt              ← pip install -r requirements.txt
.env.example                  ← انسخوه .env واملأوا القيم
09_docs/ollama_setup_guide.md ← تثبيت Ollama + تحميل الموديل الأساسي
```

---

## المرحلة 1 — جمع البيانات (نقطة انطلاق المسارين معًا)
```
01_scraping/scrape_iti.py
01_scraping/scrape_nti.py
01_scraping/scrape_depi.py              ← ابدأوا بيه، فيه بيانات مجمّعة فعلاً كمرجع
01_scraping/pdf_extractor.py
01_scraping/scrape_facebook_pages.py    ← مهم جدًا هنا، ده مصدر أسئلة الـFine-tuning
01_scraping/scheduler.py
```
**المخرج:** `02_data/01_raw/{iti,nti,depi}/{official,community}/`

---

## من هنا المسار بيتفرع لاتنين بالتوازي 👇

### مسار (أ): RAG — من المستندات الرسمية
```
03_rag_pipeline/preprocessing/clean_text.py     1
03_rag_pipeline/preprocessing/deduplicate.py    2
03_rag_pipeline/preprocessing/chunker.py        3   → المخرج: 02_data/04_chunks/
03_rag_pipeline/embeddings/model_benchmark.py   4   (قارنوا الموديلات الأول)
03_rag_pipeline/embeddings/vector_db_config.py  5
03_rag_pipeline/embeddings/embed_and_store.py   6
03_rag_pipeline/retrieval/retriever.py          7
03_rag_pipeline/retrieval/reranker.py           8   (اختياري)
```
**المدخل:** بيانات `official/` بس من `01_raw` (مستندات، PDFs، صفحات رسمية).
**المخرج النهائي:** Vector DB جاهزة.

### مسار (ب): Fine-tuning — من الأسئلة الحقيقية
```
02_data/02_qa_pairs/*.jsonl                     0   ← جمّعوا/نظفوا هنا أسئلة الفيسبوك والمجتمع يدويًا أو شبه-تلقائي
04_finetuning_pipeline/prepare_dataset.py       1   ← يحول qa_pairs لصيغة instruction/response
04_finetuning_pipeline/Modelfile                2   ← يحدد الموديل الأساسي + الـsystem prompt
04_finetuning_pipeline/train_finetune.py        3
04_finetuning_pipeline/evaluate_finetune.py     4   ← تأكدوا إنه بيحافظ على الأسلوب من غير اختلاق حقائق
```
**المدخل:** بيانات `community/` بشكل أساسي من `01_raw` (أسئلة حقيقية، تعليقات).
**المخرج النهائي:** موديل Ollama مضبوط (fine-tuned) بأسلوب رد مصري.

> **ملاحظة:** المسارين ممكن يشتغلوا بالتوازي بفريقين فرعيين من نفس التيم، لأن مفيش اعتمادية مباشرة بين الاتنين غير إنهم بياخدوا من نفس `01_raw`.

---

## المرحلة 3 — الالتقاء (بعد ما المسارين يخلصوا)
```
05_generation/ollama_client.py       1   ← بيستدعي الموديل المضبوط من مسار (ب)
05_generation/prompt_templates.py    2   ← بيستقبل الـcontext من مسار (أ)
05_generation/generate_answer.py     3   ← نقطة الدمج الفعلية: موديل مضبوط + context من RAG
```

---

## المرحلة 4 — الواجهة + التقييم + التوثيق
```
07_evaluation/test_questions.jsonl        1
07_evaluation/evaluate_retrieval.py       2   (يقيس مسار RAG بس)
07_evaluation/evaluate_answers.py         3   (يقيس الإجابة الكاملة: أسلوب + دقة)
07_evaluation/model_comparison_results.md 4
06_app/main.py                            5
06_app/api.py                             6
06_app/ui/                                7
08_logs/unanswered_questions.log          (تلقائي وقت التشغيل)
README.md                                 آخر حاجة تحدثوها
```

---

## ملفات مرجعية بس (للقراءة، متتكتبش فيها كود)
```
09_docs/data_dictionary.md
09_docs/ollama_setup_guide.md
09_docs/project_roadmap_ollama.md
09_docs/project_split_5_parts.md
02_data/01_raw/depi/official/depi_raw_data_collected.md   ← بيانات DEPI الجاهزة
```

---

## خلاصة الترتيب السريع

**1 (scraping) → يتفرع لـ [أ: RAG] و [ب: Fine-tuning] بالتوازي → 3 (الدمج في 05_generation) → 4 (app + evaluation)**

تنبيه أخير: بيانات الـFine-tuning (مسار ب) لازم تركز على **الأسلوب** مش الحقائق، عشان لو المعلومة الرسمية اتغيرت، الموديل ميفضلش متمسك بمعلومة قديمة اتحفظت في أوزانه — الحقائق مصدرها الوحيد الدايم هو RAG (مسار أ).
