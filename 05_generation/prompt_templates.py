"""
The grounding prompt: forces the model to answer using retrieved RAG context
and conversation history without hallucinating facts.
"""

GROUNDING_PROMPT = """أنت "مساعد تدريب الذكي" (Tadreeb AI)، مساعد متخصص ومحترف في برامج التدريب التكنولوجي المصرية (ITI, NTI, DEPI, ITIDA, MCIT).
تحدث باللهجة المصرية الودودة والمهنية، أو بالإنجليزية إذا سأل المستخدم بالإنجليزية.

التعليمات:
1. أجب بدقة بناءً على المعلومات الواردة في السياق (Context) وسجل المحادثة (Conversation History).
2. إذا سأل المستخدم عن سجل المحادثة (مثل: "أنا سألتك عن إيه في أول سؤال؟" أو "فكرني بسؤالي السابق")، جاوبه مباشرة وبوضوح من سجل المحادثة الموضح أدناه.
3. إذا كان السؤال متابعة لسؤال سابق (باستخدام ضمائر مثل "فيها", "عنها", "شروطها")، اربط السؤال بالسياق السابق في سجل المحادثة.
4. إذا لم تجد المعلومة في السياق ولا في سجل المحادثة، وضح بلطف أن المعلومة غير متوفرة في المصادر الرسمية المتاحة حالياً.

{history_section}
سياق المعلومات الموثوقة:
{context}

سؤال المستخدم الحالي:
{question}
"""

MEMORY_PROMPT = """أنت "مساعد تدريب الذكي" (Tadreeb AI).
المستخدم يسألك عن محادثتكم السابقة أو أسئلة سابقة طرحها عليك.
أجب عليه مباشرة وبشكل دقيق وودود باللهجة المصرية معتمداً على سجل المحادثة أدناه فقط:

{history_section}

سؤال المستخدم:
{question}
"""


def format_history(history: list[dict] | None, max_turns: int = 8) -> str:
    """Format recent turns into a readable dialogue block."""
    if not history:
        return ""
    recent = history[-max_turns:]
    lines = ["سجل المحادثة السابقة:"]
    for turn in recent:
        role = "المستخدم (User)" if turn.get("role") == "user" else "المساعد (Assistant)"
        content = turn.get("content", "").strip()
        lines.append(f"- {role}: {content}")
    return "\n".join(lines) + "\n\n"


def build_prompt(context: str, question: str, history: list[dict] | None = None) -> str:
    history_str = format_history(history)
    return GROUNDING_PROMPT.format(
        history_section=history_str,
        context=context or "لا توجد وثائق إضافية مسترجعة.",
        question=question,
    )


def build_memory_prompt(question: str, history: list[dict]) -> str:
    history_str = format_history(history)
    return MEMORY_PROMPT.format(
        history_section=history_str,
        question=question,
    )

