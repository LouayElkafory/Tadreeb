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
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text
   ```

4. Copy `.env.example` to `.env` and adjust values if needed.

## Building the RAG index and starting the app

Run each pipeline stage once, in order, from the project root:

```bash
cd 01_scraping && python pdf_extractor.py && cd ..
cd 03_rag_pipeline/preprocessing && python clean_text.py && python deduplicate.py && python chunker.py && cd ../..
cd 03_rag_pipeline/embeddings && python embed_and_store.py && cd ../..
cd 04_finetuning_pipeline && python prepare_dataset.py && cd ..
```

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
backend -> RAG pipeline -> ChromaDB -> Qwen/Ollama).

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

## Data and Model Responsibilities

Fine-tuning data should primarily teach response style, tone, and conversational
behavior. Avoid placing facts that may change, such as application deadlines,
eligibility requirements, or contact details, in the fine-tuning dataset. These
facts should be retrieved from official sources at response time through the RAG
pipeline. This separation reduces the risk of producing outdated answers.

## Team

NTI NLP Track - Team 4
