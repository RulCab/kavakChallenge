def extract_topic_from_seed(seed: str) -> str:
    out = seed
    if out.startswith("I will prove that "):
        out = out[len("I will prove that "):]
    return out.rstrip("!")

def is_on_topic(user_msg: str, topic: str) -> bool:
    topic_kw = {w.lower() for w in topic.split() if len(w) > 3}
    msg_kw = {w.lower() for w in user_msg.split() if len(w) > 3}
    return len(topic_kw & msg_kw) >= max(1, len(topic_kw) // 6)

def ground_reply(topic: str) -> str:
    return (
        f"Let's stay on our topic: **{topic}**. "
        "I’ll address your point strictly in relation to this claim."
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
