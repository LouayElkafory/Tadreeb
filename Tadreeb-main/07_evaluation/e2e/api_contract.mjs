// End-to-end test: drives the backend exactly as the browser does - same URL,
// same Origin header, same payload shape as src/services/chatApi.ts - then
// validates every response against the Source contract in src/types/index.ts
// the way SourceCard actually renders it.
const API = "http://localhost:8000";
const ORIGIN = "http://localhost:5173";
const SOURCE_TYPES = ["official", "government", "document", "community"];

const localize = (v, lang) => (v == null ? undefined : v[lang]); // useLanguage().localize

let pass = 0,
  fail = 0;
const track = (ok) => (ok ? pass++ : fail++);

// The fine-tuned model is Qwen-based and leaks CJK. Checked on EVERY answer.
const CJK = /[぀-ヿ㐀-䶿一-鿿]/g;

function checkScript(answer, label) {
  const bad = answer.match(CJK);
  if (bad) {
    console.log(`  FAIL ${label}: CJK characters in answer -> ${[...new Set(bad)].join("")}`);
    return false;
  }
  console.log(`  PASS ${label}: no stray scripts`);
  return true;
}

function validate(data, label) {
  const problems = [];
  if (typeof data.answer !== "string" || !data.answer.trim()) problems.push("answer missing/empty");
  if (!Array.isArray(data.sources)) problems.push("sources not an array");
  if (!Array.isArray(data.suggested_questions)) problems.push("suggested_questions not an array");

  (data.sources || []).forEach((s, i) => {
    if (typeof s.id !== "string") problems.push(`sources[${i}].id not a string`);
    if (!SOURCE_TYPES.includes(s.type))
      problems.push(`sources[${i}].type "${s.type}" outside SourceType union -> SourceCard crashes on config.icon`);
    for (const field of ["title", "organization", "description"]) {
      if (field === "description" && s[field] === undefined) continue;
      for (const lang of ["ar", "en"]) {
        const v = localize(s[field], lang);
        if (typeof v !== "string" || !v)
          problems.push(`sources[${i}].${field}.${lang} renders as ${JSON.stringify(v)} -> blank in UI`);
      }
    }
    if (typeof s.url !== "string") problems.push(`sources[${i}].url not a string`);
  });

  if (problems.length) {
    console.log(`  FAIL ${label}:\n    - ` + problems.join("\n    - "));
    return false;
  }
  console.log(`  PASS ${label}`);
  return true;
}

async function chat(message, history = [], language = "ar") {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Origin: ORIGIN },
    body: JSON.stringify({ message, conversation_id: "e2e-1", language, history }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const allowed = res.headers.get("access-control-allow-origin");
  if (allowed !== ORIGIN) throw new Error(`CORS header missing/wrong: ${allowed}`);
  return res.json();
}

// --- 1. grounded Arabic question -------------------------------------------
console.log("\n[1] Arabic factual question");
let d = await chat("كورس DevOps Engineer في DEPI مدته كام ساعة؟");
console.log("  answer:", d.answer.slice(0, 90));
console.log("  sources:", d.sources.map((s) => `${s.organization.ar} / ${s.title.ar}`).join(" | "));
track(validate(d, "response shape"));
track(checkScript(d.answer, "script purity"));
track(
  /DevOps/i.test(d.answer)
    ? (console.log("  PASS track name kept in Latin script"), true)
    : (console.log("  FAIL 'DevOps' transliterated or dropped"), false)
);
track(
  d.answer.includes("162")
    ? (console.log("  PASS grounded fact 162 present"), true)
    : (console.log("  FAIL expected 162 in answer"), false)
);

// --- 2. English question -> English answer ---------------------------------
console.log("\n[2] English question (language pinning)");
d = await chat("How many hours is the technical skills track in the ITIDA summer training?", [], "en");
console.log("  answer:", d.answer.slice(0, 90));
track(validate(d, "response shape"));
track(checkScript(d.answer, "script purity"));
track(
  !/[ء-ي]/.test(d.answer)
    ? (console.log("  PASS answered in English only"), true)
    : (console.log("  FAIL Arabic text in an English answer"), false)
);
track(
  d.answer.includes("90")
    ? (console.log("  PASS grounded fact 90 present"), true)
    : (console.log("  FAIL expected 90 in answer"), false)
);

// --- 3. multi-turn follow-up (history sent exactly as useChat builds it) ----
console.log("\n[3] Multi-turn follow-up");
const q1 = "احكيلي عن برامج معهد تكنولوجيا المعلومات ITI";
const r1 = await chat(q1);
const history = [
  { role: "user", content: q1 },
  { role: "assistant", content: r1.answer },
];
d = await chat("طب إيه شروط التقديم فيها؟", history);
console.log("  answer:", d.answer.slice(0, 90));
const orgs = [...new Set(d.sources.map((s) => s.organization.ar))];
track(validate(d, "response shape"));
track(checkScript(d.answer, "script purity"));
track(
  orgs.length === 1 && orgs[0] === "ITI"
    ? (console.log("  PASS follow-up resolved to ITI sources only"), true)
    : (console.log(`  FAIL follow-up resolved to ${orgs.join(", ")}`), false)
);

// --- 4. conversation memory ------------------------------------------------
console.log("\n[4] Conversation memory");
const history2 = [
  ...history,
  { role: "user", content: "طب إيه شروط التقديم فيها؟" },
  { role: "assistant", content: d.answer },
];
d = await chat("أنا سألتك في أول سؤال عن إيه؟", history2);
console.log("  answer:", d.answer.slice(0, 90));
track(checkScript(d.answer, "script purity"));
track(
  /ITI|معهد تكنولوجيا/.test(d.answer)
    ? (console.log("  PASS recalled the first question"), true)
    : (console.log("  FAIL did not recall the first question"), false)
);

// --- 5. out-of-corpus -> refusal, no sources -------------------------------
console.log("\n[5] Out-of-corpus question");
d = await chat("إزاي أطبخ كشري؟");
console.log("  answer:", d.answer.slice(0, 90));
track(
  d.sources.length === 0 && d.answer.includes("مش لاقي")
    ? (console.log("  PASS refused with no sources"), true)
    : (console.log(`  FAIL answered anyway with ${d.sources.length} source(s)`), false)
);

console.log(`\n==== ${pass} passed, ${fail} failed ====`);
process.exit(fail ? 1 : 0);
