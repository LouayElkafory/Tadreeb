"""
The grounding prompt: forces the model to answer from retrieved context and
conversation history instead of from its own parametric memory.

Two changes here matter for hallucination:

* Context blocks are numbered and labelled with their source. An unlabelled
  concatenation of chunks gave the model no way to tell DEPI's material from
  ITI's, and it blended them.
* The instructions say explicitly that everything outside the context is
  off-limits, and name the specific things it was inventing - hours, dates,
  fees, links, deadlines. "Answer accurately based on the context" was not a
  strong enough constraint on a small local model.
* The reply language is pinned, in that language, at the end of the prompt. The
  fine-tuned model is Qwen-based and would otherwise drop into Chinese
  mid-answer, and an all-Arabic prompt pulled English questions into Arabic.
"""
import re

GROUNDING_PROMPT = """أنت "مساعد تدريب الذكي" (Tadreeb AI)، مساعد متخصص في برامج التدريب التكنولوجي المصرية (ITI, NTI, DEPI, ITIDA, MCIT).

قواعد إلزامية:
1. اعتمد فقط على "المصادر" الموضحة تحت وسجل المحادثة. ممنوع تماماً تستخدم معلومات من معرفتك العامة.
2. ما تخترعش أي رقم أو مدة أو عدد ساعات أو تاريخ أو موعد تقديم أو رسوم أو رابط أو إيميل مش مكتوب حرفياً في المصادر.
3. لو المصادر فيها جزء من الإجابة بس، قول الجزء اللي عندك ووضح إيه اللي مش متاح.
4. لو المصادر مفيهاش إجابة على السؤال، قول صراحة إن المعلومة مش متوفرة في المصادر الرسمية المتاحة، وما تحاولش تخمن.
5. خلي بالك من اسم الجهة في كل مصدر: ما تنسبش معلومة خاصة بجهة لجهة تانية.
6. رد باللهجة المصرية الودودة، أو بالإنجليزية لو المستخدم سأل بالإنجليزية. الحد الأقصى 5 جمل قصيرة أو 5 نقاط، وما تكررش معلومة أو جملة.

{history_section}المصادر المتاحة:
{context}

سؤال المستخدم:
{question}

{language_directive}

{answer_cue}"""

MEMORY_PROMPT = """أنت "مساعد تدريب الذكي" (Tadreeb AI).
المستخدم بيسألك عن محادثتكم السابقة. جاوب من سجل المحادثة اللي تحت بس، باللهجة المصرية، وما تضيفش أي حاجة مش مكتوبة فيه.

{history_section}
سؤال المستخدم:
{question}

الإجابة:"""

MEMORY_PROMPT_EN = """You are Tadreeb AI.
The user is asking about the previous conversation. Answer only from the conversation history below, in English, without adding anything that is not written there.

{history_section}
User question:
{question}

Answer:"""

ORG_LABELS = {"iti": "ITI", "nti": "NTI", "depi": "DEPI", "itida": "ITIDA"}

_ARABIC = re.compile("[ء-ي]")  # letters only; ؀-ۿ also covers Arabic punctuation
_LATIN = re.compile("[A-Za-z]")

# Stated in the target language - an instruction written in Arabic is much
# weaker at keeping the model in English, and vice versa.
LANGUAGE_DIRECTIVE = {
    "ar": (
        "اكتب الإجابة باللغة العربية (اللهجة المصرية) فقط. "
        "ممنوع تماماً تستخدم الحروف الصينية أو أي حروف غير العربية والإنجليزية. "
        "اكتب أسماء البرامج والمسارات والتقنيات بالإنجليزية زي ما هي "
        "(مثل DevOps Engineer، DEPI، ITI، Data Scientist) وما تترجمهاش وما تكتبهاش بحروف عربية. "
        "ماتنسخش أو تكتب جمل شرح بالإنجليزية؛ الإنجليزي مسموح لأسماء البرامج والمسارات والتقنيات فقط."
    ),
    "en": (
        "Write the entire answer in English only. Do not use Arabic, Chinese, "
        "or any other script. Keep programme, track and technology names exactly "
        "as written in the sources (DevOps Engineer, DEPI, ITI). Use at most five "
        "short sentences or five bullet points, with no repeated facts."
    ),
}

ANSWER_CUE = {
    "ar": "الإجابة (من المصادر فقط):",
    "en": "Answer (from the sources only):",
}

# A broad question ("عاوز أعرف تفاصيل عن ITI") asks for an overview, not for the
# one fact that matched best. Retrieval now returns a wider, more varied set of
# chunks for these; this tells the model to organise them into sections instead
# of answering with the first one. The "only what's in the sources" rule still
# applies - a section with nothing behind it is left out, not filled in.
STRUCTURE_DIRECTIVE = {
    "ar": (
        "ده سؤال عام، فرتب الإجابة في نقاط قصيرة تحت عناوين زي: تعريف الجهة، "
        "البرامج والتراكات المتاحة، مدة التدريب، نوع التدريب، الفئة المستهدفة، "
        "شروط التقديم، طريقة التقديم، المصادر. "
        "سيب أي عنوان مفيش عنه معلومة في المصادر - ما تملاهوش من عندك."
    ),
    "en": (
        "This is a broad question, so organise the answer as short bullet points "
        "under headings such as: what the organisation is, available programs and "
        "tracks, training duration, training type, target audience, eligibility, "
        "how to apply, sources. Leave out any heading the sources say nothing "
        "about - do not fill it in yourself."
    ),
}
COMPARISON_DIRECTIVE = {
    "ar": (
        "ده سؤال مقارنة، فقارن بين الجهات نقطة بنقطة (الهدف، البرامج، المدة، "
        "الفئة المستهدفة، شروط التقديم) من المصادر بس، وما تقارنش في حاجة "
        "المصادر ساكتة عنها."
    ),
    "en": (
        "This is a comparison question: compare the organisations point by point "
        "(purpose, programs, duration, target audience, eligibility) using the "
        "sources only, and skip any point the sources do not cover."
    ),
}
# A question about one specific field deserves one specific answer. Without this
# the model pads a one-line duration answer with the whole track description,
# because the retrieved context contains it.
FOCUSED_DIRECTIVE = {
    "ar": (
        "السؤال ده عن نقطة واحدة محددة، فجاوب عليها في سطر أو سطرين من المصادر "
        "بس، وما تزودش تفاصيل مش مطلوبة. لو المصادر مش بتقول الرقم أو الشرط "
        "المطلوب بالحرف، قول إنه مش موجود في المصادر."
    ),
    "en": (
        "This question is about one specific detail: answer it in one or two "
        "lines from the sources only, without padding it with unrelated detail. "
        "If the sources do not state that figure or rule explicitly, say so."
    ),
}

# Intents that get extra shaping; everything else uses the plain instructions.
STRUCTURED_INTENTS = {
    "overview": STRUCTURE_DIRECTIVE,
    "comparison": COMPARISON_DIRECTIVE,
    "duration": FOCUSED_DIRECTIVE,
    "training_type": FOCUSED_DIRECTIVE,
    "eligibility": FOCUSED_DIRECTIVE,
    "application": FOCUSED_DIRECTIVE,
}


def detect_language(text: str) -> str:
    """Pick the reply language from the question itself ("ar" or "en")."""
    arabic = len(_ARABIC.findall(text))
    latin = len(_LATIN.findall(text))
    if arabic == 0 and latin == 0:
        return "ar"
    # Arabic questions routinely carry English track names ("DevOps Engineer"),
    # so any real amount of Arabic means the user is writing Arabic.
    return "ar" if arabic >= max(3, latin * 0.2) else "en"


def resolve_language(question: str, requested: str | None = None) -> str:
    """The question's own language wins; `requested` only breaks a tie."""
    detected = detect_language(question)
    if requested in ("ar", "en") and not _ARABIC.search(question) and not _LATIN.search(question):
        return requested
    return detected


def format_context(chunks: list[dict]) -> str:
    """Number each chunk and label it with the organisation and document it came from."""
    if not chunks:
        return "لا توجد مصادر متاحة."
    blocks = []
    for number, chunk in enumerate(chunks, start=1):
        org = ORG_LABELS.get(str(chunk.get("org", "")).lower(), str(chunk.get("org", "")).upper())
        source = chunk.get("title") or chunk.get("document") or "مصدر رسمي"
        page = chunk.get("page")
        label = f"[{number}] {org} - {source}" + (f" (صفحة {page})" if page else "")
        blocks.append(f"{label}\n{chunk.get('text', '').strip()}")
    return "\n\n".join(blocks)


def format_history(history: list[dict] | None, max_turns: int = 6) -> str:
    """Format recent turns into a readable dialogue block."""
    if not history:
        return ""
    lines = ["سجل المحادثة السابقة:"]
    for turn in history[-max_turns:]:
        role = "المستخدم" if turn.get("role") == "user" else "المساعد"
        content = (turn.get("content") or "").strip()
        if content:
            lines.append(f"- {role}: {content}")
    return "\n".join(lines) + "\n\n"


def build_prompt(
    chunks: list[dict],
    question: str,
    history: list[dict] | None = None,
    language: str | None = None,
    intent: str | None = None,
) -> str:
    """`intent` comes from query_understanding.analyze(); it only adds shaping
    instructions for broad questions, and the prompt is unchanged without it."""
    resolved = resolve_language(question, language)
    directive = LANGUAGE_DIRECTIVE[resolved]
    structure = STRUCTURED_INTENTS.get(intent or "")
    if structure:
        directive = f"{structure[resolved]}\n\n{directive}"
    return GROUNDING_PROMPT.format(
        history_section=format_history(history),
        context=format_context(chunks),
        question=question,
        language_directive=directive,
        answer_cue=ANSWER_CUE[resolved],
    )


def build_memory_prompt(question: str, history: list[dict], language: str = "ar") -> str:
    template = MEMORY_PROMPT_EN if language == "en" else MEMORY_PROMPT
    return template.format(
        history_section=format_history(history, max_turns=12),
        question=question,
    )
