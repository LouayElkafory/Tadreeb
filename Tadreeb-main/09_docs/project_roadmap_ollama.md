# خارطة الطريق (نسخة Ollama / Local LLM)
## RAG Chatbot لبرامج وزارة الاتصالات (ITI / NTI / رواد مصر الرقمية) — بدون API خارجي

> الفرق الأساسي عن النسخة اللي فاتت: بدل ما نبعت للـLLM أو الـembedding model عن طريق API (OpenAI مثلاً)، هنشغّل كل حاجة **محليًا على جهازكم/سيرفر الفريق** باستخدام **Ollama**. ده معناه: مفيش تكلفة API، مفيش اعتماد على إنترنت وقت الاستخدام، بس محتاجين هارد وير كويس (GPU يفضل) وصبر أكتر شوية في الإعداد.

---

## 1. الفرق الجوهري في الـArchitecture

| العنصر | النسخة اللي فاتت (API) | النسخة دي (Ollama) |
|---|---|---|
| LLM للإجابة | OpenAI GPT / Claude API | نموذج محلي عبر Ollama (مثلاً `llama3.1`, `qwen2.5`, `aya-expanse`, `command-r`) |
| Embedding Model | OpenAI `text-embedding-3` | نموذج embedding محلي عبر Ollama (`nomic-embed-text`, `mxbai-embed-large`) أو مكتبة منفصلة (`sentence-transformers`) |
| التكلفة | حسب الاستخدام (Pay-per-token) | مجاني بعد التجهيز، لكن محتاج موارد Hardware |
| الاتصال بالإنترنت وقت الرد | مطلوب | غير مطلوب (كل حاجة local) |
| الخصوصية | البيانات بتتبعت لسيرفر خارجي | البيانات كلها فضلت جوه جهازكم |
| الأداء مع العربي | أقوى غالبًا (خصوصًا Claude/GPT-4) | لازم اختيار نموذج بعناية — مش كل نماذج Ollama كويسة في العربي المصري |

---

## 2. أهم تحدي هتقابلوه: اختيار الموديل الصح للعربي

ده أهم قرار في النسخة دي. مش كل نموذج متاح على Ollama بيفهم اللهجة المصرية كويس. رشحلكم نبدأوا نجرب بالترتيب ده:

### للـ Generation (توليد الإجابة):
1. **`qwen2.5` (7B أو 14B)** — من أقوى النماذج المفتوحة حاليًا في العربي الفصحى واللهجات، ومتاح على Ollama مباشرة.
2. **`aya-expanse`** (من Cohere) — مبني أساسًا لدعم لغات متعددة بما فيها العربي.
3. **`command-r`** — كويس في مهام الـRAG تحديدًا (مبني أصلاً عشان الـretrieval-augmented tasks).
4. **`llama3.1` (8B)** — خيار احتياطي، لكن أداءه في العربي أضعف من Qwen وAya غالبًا.

> **نصيحة:** اعملوا اختبار سريع (10-15 سؤال حقيقي من اللي جمعناه) على كل نموذج قبل ما تقرروا، ومتفترضوش إن نموذج معين هيبقى كويس من الاسم بس.

### للـ Embeddings:
1. **`nomic-embed-text`** — متاح مباشرة على Ollama، بيدعم multilingual بشكل معقول.
2. لو الأداء العربي مش كفاية، بديل قوي (مش عن طريق Ollama لكن local برضو): مكتبة `sentence-transformers` مع موديل `intfloat/multilingual-e5-large` — شغال بالكامل offline وبيعتبر من أقوى الخيارات المجانية للعربي حاليًا.

**القرار العملي:** ابدأوا بـ`nomic-embed-text` عشان السهولة، ولو الـretrieval quality ضعيف في الاختبار، حولوا لـ`multilingual-e5-large` عن طريق `sentence-transformers` (ممكن تشغلوها جنب Ollama من غير مشكلة، مش لازم كل حاجة تبقى من نفس المصدر).

---

## 3. متطلبات الـHardware (مهم تحسبوها من الأول)

| الموديل | الحجم | RAM/VRAM المطلوب تقريبًا |
|---|---|---|
| `qwen2.5:7b` | 7B | ~8GB RAM (CPU) أو ~6GB VRAM (GPU) |
| `qwen2.5:14b` | 14B | ~16GB RAM أو ~10-12GB VRAM |
| `nomic-embed-text` | صغير | أقل من 2GB |
| `llama3.1:8b` | 8B | ~8-10GB RAM |

- لو معندكمش GPU، هتشتغل على CPU بس أبطأ بكتير (استجابة ممكن تاخد ثواني لدقيقة بدل أجزاء ثانية).
- بدائل مجانية لو الهاردوير محدود: Google Colab (GPU مجاني بحدود) للتجربة والتطوير، أو نموذج أصغر (3B) كبداية.

---

## 4. هيكل الفولدرات المعدّل

```
mcit-programs-chatbot/
│
├── README.md
├── requirements.txt                   # بدون مكتبات OpenAI/Anthropic SDK، بدلها: ollama, chromadb, sentence-transformers
├── .env.example                       # هنا مفيش API keys تقريبًا، لكن ممكن يفضل OLLAMA_HOST لو مش على نفس الجهاز
│
├── data/                              # (زي ما هو من غير تغيير)
│   ├── raw/{iti,nti,depi}/{official,community}/
│   ├── processed/
│   └── chunks/
│
├── scraping/                          # (زي ما هو من غير تغيير)
│
├── preprocessing/                     # (زي ما هو من غير تغيير)
│
├── embeddings/
│   ├── embed_and_store.py             # يستخدم ollama.embeddings() أو sentence-transformers محليًا
│   ├── vector_db_config.py            # ChromaDB أو Qdrant (local mode, من غير سحابة)
│   └── model_benchmark.py             # [جديد] سكربت لمقارنة أداء أكتر من embedding model على أسئلتنا
│
├── retrieval/
│   ├── retriever.py
│   └── reranker.py                    # لو هتعملوا reranking محلي، فيه نماذج صغيرة زي bge-reranker
│
├── generation/
│   ├── ollama_client.py               # [جديد] الاتصال بـ Ollama server المحلي
│   ├── prompt_templates.py
│   └── generate_answer.py             # يستدعي ollama.chat() بدل استدعاء API خارجي
│
├── app/
│   ├── main.py
│   ├── api.py
│   └── ui/                            # Streamlit/Gradio مناسبين جدًا هنا لسهولة الديمو المحلي
│
├── evaluation/
│   ├── test_questions.jsonl
│   ├── model_comparison_results.md    # [جديد] نتيجة مقارنة النماذج المختلفة على Ollama
│   ├── evaluate_retrieval.py
│   └── evaluate_answers.py
│
├── logs/
│   └── unanswered_questions.log
│
└── docs/
    ├── data_dictionary.md
    ├── ollama_setup_guide.md          # [جديد] خطوات تثبيت وتشغيل Ollama للفريق كله
    └── architecture_diagram.png
```

---

## 5. Metadata Schema

**بدون تغيير** عن النسخة اللي فاتت — نفس الحقول (`program_name`, `info_type`, `source_url`, إلخ) لأن ده مستقل تمامًا عن اختيار LLM/API مقابل Ollama.

---

## 6. خطوات الإعداد الأولى (Setup Steps)

1. **تثبيت Ollama:** تحميل من الموقع الرسمي `ollama.com` (متاح لـ Windows/Mac/Linux).
2. **تشغيل السيرفر المحلي:** `ollama serve` (بيشتغل تلقائي غالبًا بعد التثبيت).
3. **تحميل النماذج المطلوبة:**
   ```
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text
   ```
4. **اختبار سريع من الـTerminal** قبل ما تدخلوا في الكود:
   ```
   ollama run qwen2.5:7b "ايه شروط التقديم في رواد مصر الرقمية؟"
   ```
   (طبعًا هيجاوب من معرفته العامة مش من بياناتكم، الهدف بس التأكد إنه بيفهم المصري كويس).
5. **تثبيت مكتبة بايثون:** `pip install ollama chromadb sentence-transformers`
6. **ربط الكود بـOllama:** استخدام مكتبة `ollama` البايثون الرسمية للاتصال بالسيرفر المحلي بدل `openai` SDK.

---

## 7. المسار الزمني للتنفيذ (معدّل)

| المرحلة | الوصف | تغيير عن نسخة الـAPI؟ |
|---|---|---|
| 1. جمع البيانات | Scraping + PDFs + Facebook | لا تغيير |
| 2. التنظيف | Cleaning + تطبيع عربي | لا تغيير |
| 3. التقسيم (Chunking) | تقسيم semantic | لا تغيير |
| **3.5 تجهيز Ollama** | تثبيت + تحميل النماذج + اختبار سريع | **[مرحلة جديدة]** |
| 4. الـEmbedding + التخزين | عن طريق Ollama/sentence-transformers محليًا | تغيير الأداة، نفس المنطق |
| **4.5 مقارنة النماذج** | اختبار 2-3 نماذج (Qwen, Aya, Llama) على عينة أسئلة حقيقية واختيار الأنسب | **[مرحلة جديدة، مهمة جدًا]** |
| 5. بناء الـRetrieval | زي ما هو | لا تغيير كبير |
| 6. بناء الـGeneration | عن طريق `ollama.chat()` بدل API | تغيير الأداة |
| 7. التقييم | زي ما هو، لكن قارنوا جودة الإجابة مقابل نسخة API (لو جربتوها) | إضافة مقارنة |
| 8. الواجهة + النشر | Streamlit/Gradio محلي، أو نشر على سيرفر الفريق | لازم تفكروا فين هيتنشر (سيرفر بمواصفات كافية) |
| 9. الصيانة الدورية | زي ما هي | لا تغيير |

---

## 8. تنبيهات مهمة قبل ما تلتزموا بالقرار ده

- **جودة الإجابة غالبًا هتبقى أضعف** من نموذج زي GPT-4/Claude في فهم الأسئلة المعقدة أو الغامضة، خصوصًا في العربي المصري العامي. لو الميزانية بتسمح، فكروا في **حل هجين**: Ollama للتطوير والتجربة (مجاني)، وAPI خارجي في النسخة النهائية لو الجودة فرق كبير.
- اختبروا الـLatency (زمن الاستجابة) بدري — لو هتعرضوا المشروع لايف قدام لجنة، بطء الاستجابة على CPU ممكن يبوظ العرض.
- سجلوا كل نتائج مقارنة النماذج في `evaluation/model_comparison_results.md` — ده هيبقى جزء قوي جدًا لو هتقدموا المشروع كمشروع تخرج/مسابقة، لأنه بيوري إنكم اتخذتوا قرار مبني على تجربة فعلية مش افتراض.
