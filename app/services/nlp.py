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

def parse_topic_and_stance(user_msg: str) -> Tuple[str, str]:
    """
    Regresa (topic, stance) a partir del primer mensaje del usuario.
    Reglas simples, robustas a español/inglés y variantes comunes:
      - "convénceme de que A es mejor que B"  -> topic: "A vs B"; stance: "A es mejor que B"
      - "convenceme de que A es mejor que B" (sin acento) idem
      - "demuéstrame que ..." / "prove that ..." idem
      - Si no matchea nada: topic = user_msg limpio; stance = user_msg limpio.
    """
    text = user_msg.strip()
    # Normaliza comillas raras y espacios
    text = re.sub(r"\s+", " ", text)

    # 1) patrón 'A es mejor que B'
    m = re.search(r'(?i)(que\s+)?(?P<a>[^.?!]+?)\s+es\s+mejor\s+que\s+(?P<b>[^.?!]+)', text)
    if m:
        a = m.group('a').strip(' "\'').rstrip('.')
        b = m.group('b').strip(' "\'').rstrip('.')
        topic = f"{a} vs {b}"
        stance = f"{a} es mejor que {b}"
        return (topic, stance)

    # 2) patrón directo: 'la tierra es plana' / 'the earth is flat'
    #  -> la stance es toda la afirmación; topic igual (genérico)
    m2 = re.search(r'(?i)(conv[ée]nceme\s+de\s+que|demu[ée]strame\s+que|prove\s+that)\s+(?P<c>.+)', text)
    if m2:
        c = m2.group('c').strip(' "\'').rstrip('.')
        # stance = la cláusula c; topic = c (o una simplificación)
        return (c, c)

    # 3) fallback: usa todo el mensaje como stance/topic
    return (text.rstrip('.'), text.rstrip('.'))
