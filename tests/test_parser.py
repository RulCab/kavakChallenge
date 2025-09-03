from app.services.nlp import extract_topic_from_seed

def test_extract_topic_from_seed():
    seed = "I will prove that football is the best sport!"
    topic = extract_topic_from_seed(seed)
    assert topic == "football is the best sport"
