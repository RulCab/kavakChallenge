import re
from typing import Tuple

def extract_topic_from_seed(seed: str) -> str:
    out = seed
    if out.startswith("I will prove that "):
        out = out[len("I will prove that "):]
    return out.rstrip("!")

def is_on_topic(user_msg: str, topic: str) -> bool:
    topic_kw = {w.lower() for w in topic.split() if len(w) > 3}
    msg_kw = {w.lower() for w in user_msg.split() if len(w) > 3}
    return len(topic_kw & msg_kw) >= max(1, len(topic_kw) // 6)

def ground_reply(topic_or_claim: str) -> str:
    return (
        f"Let's stay on our original claim: **{topic_or_claim}**. "
        "I'll address your point strictly in relation to this claim."
    )

def build_prompt(topic: str, user_message: str, style: str) -> str:
    return f"""You must defend "**{topic}**" at all costs.

Guidelines:
- Stand your ground: never change your stance.
- Be persuasive: logical reasoning, examples, rhetorical techniques.
- Stay on topic: relate everything to the original claim.
- Extend the discussion: invite follow-ups.
- Keep responses concise (must complete in <30s).
- Your argument style is: **{style}**.

Conversation:
User: {user_message}
AI:"""

_PREFIXES = [
    r"conv[ée]nceme\s+de\s+que\s+",
    r"convenceme\s+de\s+que\s+",
    r"demu[ée]strame\s+que\s+",
    r"demuestrame\s+que\s+",
    r"pru[ée]bame\s+que\s+",
    r"pruebame\s+que\s+",
    r"prove\s+that\s+",
]

_PREFIX_RE = re.compile(rf"(?i)^(?:{'|'.join(_PREFIXES)})")

def _strip_prefix(text: str) -> str:
    t = text.strip()
    return _PREFIX_RE.sub("", t)

def parse_topic_and_stance(user_msg: str) -> Tuple[str, str]:
    """
    (topic, stance) desde el 1er mensaje.
      - "Convénceme de que A es mejor que B" -> topic="A vs B"; stance="A es mejor que B"
      - "La tierra es plana" -> topic="La tierra es plana"; stance igual
      - Si no matchea: topic = stance = mensaje limpio.
    """
    original = user_msg.strip()
    text = re.sub(r"\s+", " ", original)
    core = _strip_prefix(text)  # quita 'convenceme de que', 'prove that', etc.

    # 1) patrón 'A es mejor que B'
    m = re.search(r'(?i)\b(?P<a>[^.?!]+?)\s+es\s+mejor\s+que\s+(?P<b>[^.?!]+)', core)
    if m:
        a = m.group('a').strip(' "\'').rstrip('.')
        b = m.group('b').strip(' "\'').rstrip('.')
        topic = f"{a} vs {b}"
        stance = f"{a} es mejor que {b}"
        return (topic, stance)

    # 2) si el usuario afirma algo directo, usa la cláusula completa como claim
    if core:
        c = core.strip(' "\'').rstrip('.')
        return (c, c)

    # 3) fallback
    c = original.strip(' "\'').rstrip('.')
    return (c, c)
