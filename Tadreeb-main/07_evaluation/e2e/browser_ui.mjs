// Real-browser end-to-end test. Launches headless Chrome, loads the Vite dev
// server, types a question into the actual chat UI, and reads the rendered DOM.
// This is the only check that proves SourceCard renders non-empty titles - a
// plain-string `title` from the API produces `undefined` via localize() and
// shows a blank card with no error anywhere.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const APP = process.env.APP_URL || "http://localhost:5173/chat";
const CHROME =
  process.env.CHROME_PATH ||
  [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ].find((candidate) => existsSync(candidate)) ||
  "chrome";
const PORT = 9222;
const profile = mkdtempSync(join(tmpdir(), "cdp-"));

let pass = 0, fail = 0;
const check = (ok, label, extra = "") => {
  console.log(`  ${ok ? "PASS" : "FAIL"} ${label}${extra ? ` -> ${extra}` : ""}`);
  ok ? pass++ : fail++;
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  "--no-first-run", "--no-default-browser-check", "--disable-gpu",
  "--window-size=1400,1000", "about:blank",
], { stdio: "ignore" });

async function targets() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await r.json();
      const page = list.find((t) => t.type === "page");
      if (page) return page;
    } catch {}
    await sleep(500);
  }
  throw new Error("Chrome DevTools endpoint never came up");
}

const page = await targets();
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let id = 0;
const pending = new Map();
const consoleErrors = [];
const failedRequests = [];

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
  }
  if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error")
    consoleErrors.push(msg.params.args.map((a) => a.value ?? a.description).join(" "));
  if (msg.method === "Runtime.exceptionThrown")
    consoleErrors.push("UNCAUGHT: " + (msg.params.exceptionDetails?.exception?.description || "exception"));
  if (msg.method === "Network.loadingFailed")
    failedRequests.push(msg.params.errorText);
};

const send = (method, params = {}) =>
  new Promise((resolve, reject) => {
    const msgId = ++id;
    pending.set(msgId, { resolve, reject });
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });

const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || "eval failed");
  return r.result.value;
};

try {
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Page.enable");

  console.log(`\nLoading ${APP} in headless Chrome...`);
  await send("Page.navigate", { url: APP });
  await sleep(4000);

  const title = await evaluate("document.title");
  check(!!title, "page loaded", title);

  // React actually mounted?
  const rootChildren = await evaluate("document.getElementById('root')?.children.length ?? 0");
  check(rootChildren > 0, "React app mounted", `${rootChildren} root children`);

  // The chat composer is present
  const hasInput = await evaluate("!!document.querySelector('textarea')");
  check(hasInput, "chat input rendered");
  if (!hasInput) throw new Error("no textarea - cannot drive the UI");

  // Type the question the way a user does: set value via the native setter so
  // React's onChange fires, then click the send button.
  const question = "كورس DevOps Engineer في DEPI مدته كام ساعة؟";
  await evaluate(`(() => {
    const ta = document.querySelector('textarea');
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(ta, ${JSON.stringify(question)});
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`);
  await sleep(400);

  const clicked = await evaluate(`(() => {
    const ta = document.querySelector('textarea');
    const form = ta.closest('form') || ta.parentElement;
    const btn = [...form.querySelectorAll('button')].pop();
    if (!btn) return false;
    btn.click();
    return true;
  })()`);
  check(clicked, "send button clicked");

  // Wait for the assistant reply to appear in the DOM.
  let answered = false;
  for (let i = 0; i < 120; i++) {
    await sleep(1000);
    answered = await evaluate(`document.body.innerText.includes('162')`);
    if (answered) break;
  }
  check(answered, "assistant answer rendered in the DOM", answered ? "contains '162'" : "timed out after 120s");

  const bodyText = await evaluate("document.body.innerText");
  check(!/[\u3040-\u30ff\u4e00-\u9fff]/.test(bodyText), "no CJK characters on screen");
  check(/DevOps/i.test(bodyText), "track name rendered in Latin script");

  // The real point: open the sources panel and confirm cards are not blank.
  await evaluate(`(() => {
    const btn = [...document.querySelectorAll('button')].find(b => /مصادر|sources/i.test(b.getAttribute('aria-label') || b.title || ''));
    if (btn) btn.click();
    return !!btn;
  })()`);
  await sleep(1500);

  const cards = await evaluate(`(() => {
    const links = [...document.querySelectorAll('a[href]')].filter(a => a.querySelector('h4'));
    return links.map(a => ({
      title: (a.querySelector('h4')?.innerText || '').trim(),
      org:   (a.querySelector('p')?.innerText || '').trim(),
      href:  a.getAttribute('href'),
    }));
  })()`);

  console.log(`  source cards found: ${cards.length}`);
  cards.slice(0, 5).forEach((c) => console.log(`    - title="${c.title}" org="${c.org}"`));
  check(cards.length > 0, "source cards rendered");
  check(cards.every((c) => c.title.length > 0), "every source card has a non-empty title");
  check(cards.every((c) => c.org.length > 0), "every source card has a non-empty organization");

  const realErrors = consoleErrors.filter((e) => !/favicon|DevTools/i.test(e));
  check(realErrors.length === 0, "no console errors", realErrors.slice(0, 3).join(" | "));
  const realFailed = failedRequests.filter((e) => !/favicon/i.test(e));
  check(realFailed.length === 0, "no failed network requests", realFailed.slice(0, 3).join(" | "));
} finally {
  try { ws.close(); } catch {}
  chrome.kill();
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}

console.log(`\n==== browser: ${pass} passed, ${fail} failed ====`);
process.exit(fail ? 1 : 0);
