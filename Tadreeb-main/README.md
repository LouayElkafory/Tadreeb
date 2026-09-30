# MCIT Programs Chatbot

## NTI NLP Track Final Project

This project delivers an Arabic conversational assistant for questions about
Egyptian Ministry of Communications and Information Technology programs:

- Information Technology Institute (ITI)
- National Telecommunication Institute (NTI)
- Digital Egypt Youth (DEPI)

The chatbot combines two complementary approaches:

- **Retrieval-Augmented Generation (RAG):** Retrieves relevant information from
  official documents and sources so that time-sensitive facts, dates, and numbers
  are grounded in current reference material.
- **Fine-tuning:** Learns an appropriate response style and Egyptian Arabic
  conversational tone from real user questions and answers. Fine-tuning is not
  used as the source of truth for changing facts.

## Project Architecture

| Directory | Purpose |
| --- | --- |
| `01_scraping` | Collects raw information from official and community sources. |
| `02_data` | Stores raw data, question-answer pairs, processed text, and chunks. |
| `03_rag_pipeline` | Cleans, deduplicates, chunks, embeds, and retrieves documents. |
| `04_finetuning_pipeline` | Prepares the dataset, fine-tunes the model, and evaluates it. |
| `05_generation` | Combines the fine-tuned model with retrieved context to generate answers. |
| `06_app` | Contains the application interface and API. |
| `07_evaluation` | Evaluates retrieval quality and final answer quality. |
| `08_logs` | Stores unanswered or unsuccessful questions for later analysis. |
| `09_docs` | Contains project documentation and reference guides. |

## Setup

1. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install [Ollama](https://ollama.com/) and start the Ollama service:

   ```bash
   ollama serve
   ```

3. Download the base language model and embedding model:

   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```

4. Copy `.env.example` to `.env` and adjust values if needed.

## Building the RAG index and starting the app

Run each pipeline stage once, in order, from the project root:

```bash
python 01_scraping/pdf_extractor.py
python 03_rag_pipeline/preprocessing/clean_text.py
python 03_rag_pipeline/preprocessing/deduplicate.py
python 03_rag_pipeline/preprocessing/chunker.py
python 03_rag_pipeline/preprocessing/qa_to_chunks.py
python 03_rag_pipeline/preprocessing/build_knowledge_base.py
python 03_rag_pipeline/embeddings/embed_and_store.py
cd 04_finetuning_pipeline && python prepare_dataset.py && cd ..
```

Optionally add general public information about the four organisations from
their official websites. This one is **incremental**: it adds new chunks to the
vector DB built above and leaves every existing PDF, chunk and vector alone, so
it can be re-run whenever the sites change.

```bash
cd 01_scraping && python collect_web_data.py && cd ..
```

It processes ITI, NTI, DEPI and ITIDA in the same run and reports per
organisation; one site being unreachable does not stop the others. See
`01_scraping/README.md` for what it collects and where it writes.

If you added web data (or changed the chunks) after the index was built, refresh
the structured knowledge base and add it to the existing vector DB without
re-embedding everything:

```bash
python 03_rag_pipeline/preprocessing/build_knowledge_base.py
python 03_rag_pipeline/embeddings/backfill_structure.py
```

That writes the `Organization -> Program -> Track` hierarchy to
`02_data/05_structured/<org>_knowledge.json`, tags every existing chunk with the
category/track/duration metadata retrieval ranks on, and indexes one fact card per
program and track. It never deletes or re-embeds an existing chunk - see
`03_rag_pipeline/README.md`.

Then confirm retrieval is healthy before doing anything else:

```bash
python 07_evaluation/evaluate_retrieval.py
```

It should report a high hit rate **and** refuse every out-of-corpus question.
If it reports a warning that the collection uses `l2` distance, the index is
stale - re-run `embed_and_store.py`.

Then start the API:

```bash
cd 06_app
uvicorn api:app --reload
```

(Optional) build a custom Ollama model from `04_finetuning_pipeline/Modelfile` and
point `FINETUNED_MODEL_NAME` in `.env` at it:

```bash
cd 04_finetuning_pipeline
ollama create depi-iti-nti-assistant -f Modelfile
```

Finally, start the frontend:

```bash
cd Frontend
npm install
npm run dev
```

Set `VITE_USE_MOCK_API=false` in `Frontend/.env` once the backend is running so
the UI calls the real API instead of its mock data.

See [`09_docs/FILE_ORDER.md`](09_docs/FILE_ORDER.md) for the full file-by-file
order and [`09_docs/project_split_5_parts.md`](09_docs/project_split_5_parts.md)
for team ownership per stage.

## Recommended Execution Order

Run the project stages in the following order:

```text
01_scraping -> 02_data -> (03_rag_pipeline and 04_finetuning_pipeline)
             -> 05_generation -> 06_app -> 07_evaluation
```

The RAG and fine-tuning pipelines can be developed and executed in parallel
after the data collection stage. They are combined in `05_generation`, where
the fine-tuned model generates an answer using context retrieved from the RAG
pipeline.

For a detailed file-by-file workflow, see
[`09_docs/FILE_ORDER.md`](09_docs/FILE_ORDER.md).

## Deployment

The backend (`06_app`) and frontend (`Frontend`) deploy as two separate
services, matching the existing architecture (Frontend/Vercel -> FastAPI
backend -> RAG pipeline -> ChromaDB -> Llama/Ollama).

**Backend (any standard Python host - not a serverless function, since the
LLM/embedding steps are long-running and stateful):**

```bash
uvicorn server:app --host 0.0.0.0 --port $PORT   # run from the project root
```

`server.py` exists because `06_app` starts with a digit and can't be used as
a dotted module path (`uvicorn 06_app.main:app` is invalid). A `Procfile` at
the project root already points hosts (Render/Railway/Heroku-style) at this
command. Install `06_app/requirements.txt` for the backend service instead of
the full project `requirements.txt` - it skips the scraping/fine-tuning-only
packages.

Required environment variables are listed in `.env.example`. In production, at
minimum set:
- `FRONTEND_ORIGIN` - the deployed frontend URL(s), comma-separated.
- `VECTOR_DB_PATH` - a path on a persistent disk/volume. On hosts with an
  ephemeral filesystem, a plain local path is wiped on every deploy/restart.
- `AUTO_INDEX` - leave `false` in production; only set `true` for a
  first-time/dev setup run against an empty vector store.

**Frontend (Vercel):** set the project's Root Directory to `Frontend`, keep
the default Vite build (`npm run build`, output `dist` - see
`Frontend/vercel.json`), and set `VITE_API_URL` to the deployed backend URL
and `VITE_USE_MOCK_API=false` in the Vercel project's environment variables.

## Choosing the LLM

By default everything runs on the local Ollama model, with no key and no
internet. To use a hosted model instead - faster, and noticeably better at mixed
Arabic/English questions - set two variables in `.env`:

```bash
LLM_PROVIDER=groq        # or openai, gemini
LLM_API_KEY=...          # never commit this; .env is gitignored
LLM_MODEL=               # blank = the provider's default
```

Ollama stays the automatic fallback: if a hosted call fails for any reason, the
same prompt is retried locally rather than failing the request. You can also
split the two jobs, so the cheap query-rewriting step runs on a fast hosted model
while the grounded answer is still written locally:

```bash
QUERY_LLM_PROVIDER=groq
```

## Answer quality

Two properties are tested together, because improving one at the other's
expense is easy and useless:

- **Retrieval finds the answer** when the corpus contains it.
- **Retrieval returns nothing** when it doesn't, so the assistant says "not in
  the sources" instead of inventing one.

```bash
python 07_evaluation/evaluate_retrieval.py   # retrieval only, seconds, no LLM
python 07_evaluation/evaluate_answers.py     # full pipeline incl. the LLM, minutes
```

With the backend and frontend both running, the end-to-end tests exercise the
full chain (React UI -> FastAPI -> RAG -> Ollama):

```bash
node 07_evaluation/e2e/api_contract.mjs   # backend as the browser calls it
node 07_evaluation/e2e/browser_ui.mjs     # headless Chrome against the real UI
```

See `07_evaluation/e2e/README.md`. These catch failures invisible to either
side alone - a valid JSON response that renders as a blank source card, or a
CORS origin mismatch that surfaces only as "تعذر الاتصال بالخادم".

The test set is `07_evaluation/test_questions.jsonl`; entries marked
`expect_no_results` are deliberately outside the corpus. Retrieval thresholds
are calibrated against it, so re-run these after changing the corpus or the
embedding model. See `03_rag_pipeline/README.md` for what each threshold does
and the known limitations.

Grounding rules worth preserving when changing `05_generation`:

- An empty retrieval result must never reach the LLM. Answering "helpfully"
  without sources is what produced invented hours, dates and admission rules.
- The reply language is pinned explicitly in the prompt. The fine-tuned model
  is Qwen-based and drifts into Chinese without it.
- `LLM_NUM_CTX` must be large enough for the whole prompt. Ollama silently
  truncates the *front* of an oversized prompt, which is where the grounding
  instructions live.

## Data and Model Responsibilities

Fine-tuning data should primarily teach response style, tone, and conversational
behavior. Avoid placing facts that may change, such as application deadlines,
eligibility requirements, or contact details, in the fine-tuning dataset. These
facts should be retrieved from official sources at response time through the RAG
pipeline. This separation reduces the risk of producing outdated answers.

## Team

NTI NLP Track - Team 4
