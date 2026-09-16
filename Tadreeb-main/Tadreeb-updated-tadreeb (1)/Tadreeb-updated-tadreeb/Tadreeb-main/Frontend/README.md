# تدريب — Tadreeb AI (Frontend)

مساعد ذكي لاكتشاف فرص التدريب التقني في مصر (ITI, NTI, DEPI, MCIT).

A premium, Arabic-first (RTL) frontend for an AI training-discovery assistant, built with **React + TypeScript + Vite + Tailwind CSS**.

## Getting started

```bash
npm install
npm run dev
```

The app runs in **mock mode** by default (`VITE_USE_MOCK_API=true` in `.env`), so the entire product — chat, sources, programs, organizations — works with no backend at all.

## Connecting the real backend

1. Set `VITE_API_URL` in `.env` to your FastAPI backend URL.
2. Set `VITE_USE_MOCK_API=false`.
3. Implement `POST /api/chat` returning:

```json
{
  "answer": "...",
  "sources": [{ "title": "...", "url": "...", "organization": "...", "type": "official" }],
  "suggested_questions": ["...", "..."]
}
```

See `src/services/chatApi.ts` for the full integration layer.

## Project structure

```
src/
  components/   shared UI building blocks
  pages/        one file per route
  layouts/      MainLayout (navbar + footer)
  data/         mock organizations, programs, sources, chat responses
  services/     chatApi.ts — mock/real backend switch
  hooks/        useChat, useLocalStorage, useLanguage
  types/        shared TypeScript models
```

## Routes

`/`, `/chat`, `/organizations`, `/organizations/:id`, `/programs`, `/programs/:id`, `/sources`, `/assistant`, `/login`, `*` (404).

## Notes

- Conversations persist in `localStorage` — no backend required to keep chat history between visits.
- The hero background (`public/main.png`) is the provided cinematic artwork; do not replace it.
- `/login` is an intentionally non-functional UI placeholder — no auth backend is implemented.
- Mock answers are clearly synthetic and never claim to be real official information.

## Build

```bash
npm run build
```
