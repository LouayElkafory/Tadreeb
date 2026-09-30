# End-to-end tests (frontend ↔ backend)

These test the chain the user actually exercises: **React UI → FastAPI → RAG →
Ollama**. They are deliberately separate from the Python evaluations in
`07_evaluation/`, which test retrieval and answer quality in isolation.

They exist because the failures at this seam are invisible to both sides. The
backend returned a perfectly valid JSON response and the frontend raised no
error, yet every source card in the UI rendered **blank** — `localize()` does a
plain `value[language]` lookup, so a plain-string `title` comes back
`undefined`. Only rendering the real DOM catches that.

## Prerequisites

Both servers running, and Ollama up with the model from `FINETUNED_MODEL_NAME`:

```bash
# terminal 1 - backend (from the project root)
uvicorn server:app --host 127.0.0.1 --port 8000

# terminal 2 - frontend
cd Frontend && npm run dev
```

`Frontend/.env` must have `VITE_USE_MOCK_API=false`, otherwise the UI serves
canned mock answers and the tests pass without the backend being involved at
all.

## `api_contract.mjs`

Drives the backend exactly as `src/services/chatApi.ts` does — same URL, same
`Origin` header, same payload — and validates each response against the
`Source` contract in `src/types/index.ts` the way `SourceCard` renders it.

```bash
node 07_evaluation/e2e/api_contract.mjs
```

Covers: grounded Arabic answer, English question answered in English, a
multi-turn follow-up resolving to the right organisation, conversation memory,
and an out-of-corpus question being refused with zero sources. Every answer is
also checked for stray CJK characters — the fine-tuned model is Qwen-based and
drifts into Chinese.

No dependencies: Node 18+ has `fetch` built in.

## `browser_ui.mjs`

Launches headless Chrome over the DevTools Protocol, loads `/chat`, types a
question into the real composer, and reads the rendered DOM.

```bash
node 07_evaluation/e2e/browser_ui.mjs
```

Covers: React mounts, the answer reaches the DOM, no CJK on screen, source
cards render with non-empty titles and organisations, and no console errors or
failed network requests.

No dependencies either — Node 20+ has a built-in `WebSocket` client, so the
DevTools Protocol is driven directly without Playwright or Puppeteer.

Overrides:

- `CHROME_PATH` — browser binary, if it isn't found automatically (Chrome and
  Edge are both fine).
- `APP_URL` — defaults to `http://localhost:5173/chat`.

## Gotchas these tests were written around

- **CORS and loopback spellings.** A browser treats `http://localhost:5173` and
  `http://127.0.0.1:5173` as different origins. `FRONTEND_ORIGIN` allows both by
  default in dev; if the UI shows only "تعذر الاتصال بالخادم", check which
  spelling the browser is on and whether it's in `FRONTEND_ORIGIN`.
- **Every user-visible string in a source must be `{ar, en}`**, not a bare
  string. See `localized()` in `06_app/api.py`.
- **`SourceCard` indexes `TYPE_CONFIG[source.type]`** and immediately reads
  `config.icon`, so a `type` outside the `SourceType` union is a hard crash, not
  a blank card. The API must only ever emit `official`, `government`,
  `document`, or `community`.
