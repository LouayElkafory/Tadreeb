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

## Data and Model Responsibilities

Fine-tuning data should primarily teach response style, tone, and conversational
behavior. Avoid placing facts that may change, such as application deadlines,
eligibility requirements, or contact details, in the fine-tuning dataset. These
facts should be retrieved from official sources at response time through the RAG
pipeline. This separation reduces the risk of producing outdated answers.

## Team

NTI NLP Track - Team 4
