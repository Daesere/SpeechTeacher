from transformers import AutoModelForCausalLM, AutoTokenizer
from ..viseme_feedback.viseme_identifier import viseme_identifier

viseme_descriptions = {
    0: "Silence — neutral or closed mouth, lips relaxed.",
    1: "æ, a, ə, ʌ, ɐ — mid-open jaw, lips relaxed or slightly spread (as in 'cat', 'cup').",
    2: "ɑ, ɑː, ɒ — wide open mouth, lips relaxed or slightly rounded (as in 'father', 'cot').",
    3: "ɔ, ɔː — rounded lips, mid-open mouth, tongue slightly back (as in 'caught', 'law').",
    4: "e, eɪ, ɛ — half-open mouth, lips slightly spread, tongue mid-front (as in 'bed', 'say').",
    5: "ɜ, ɜː, ɝ, ɚ — mid-central vowel, lips slightly rounded, tongue bunched (as in 'bird', 'fur').",
    6: "j, i, iː, ɪ, ɨ — spread lips (smile shape), mouth nearly closed, tongue high/front (as in 'see', 'yes').",
    7: "w, u, uː, ʊ — rounded lips protruded forward, minimal jaw movement (as in 'boot', 'wood').",
    8: "o, oʊ, əʊ — rounded lips, slightly open, less tight than /u/ (as in 'go', 'boat').",
    9: "aʊ — jaw drops then lips round (dynamic open→rounded, as in 'now', 'out').",
    10: "ɔɪ — rounded→spread transition (as in 'boy', 'toy').",
    11: "aɪ — open→spread transition, jaw drops then lips spread (as in 'my', 'sky').",
    12: "h, ɦ — slightly open mouth, lips neutral, breathy airflow (as in 'hat').",
    13: "r, ɹ, ɾ — lips slightly rounded, corners drawn in, small opening (as in 'red').",
    14: "l, ɫ — tip of tongue on alveolar ridge, mouth slightly open (as in 'let').",
    15: "s, z — lips slightly parted, teeth nearly closed, corners retracted (as in 'see', 'zoo').",
    16: "ʃ, tʃ, dʒ, ʒ — rounded lips, jaw slightly lowered, teeth close (as in 'shoe', 'judge').",
    17: "θ, ð — tongue between teeth, lips relaxed (as in 'think', 'this').",
    18: "f, v — upper teeth on lower lip, narrow gap (as in 'fun', 'van').",
    19: "d, t, n — light tongue contact on upper ridge, lips neutral (as in 'do', 'no').",
    20: "k, g, ŋ — mouth slightly open, lips neutral, tongue back (as in 'go', 'sing').",
    21: "p, b, m — closed lips, full bilabial contact (as in 'pat', 'bat', 'man')."
}

model_name = "Qwen/Qwen-8B-Chat"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", trust_remote_code=True).eval()

base_history = "You are a phonetics coach helping learners improve pronunciation."

history = [
    {"role": "system", "content": base_history}
]


def extract_input(sentence, expected_phonemes, user_phonemes, errors):
    
    viseme_ids: tuple[str, int] = viseme_identifier(errors)
    
    input_string = f"The user pronouced the sentence \"{sentence}\" this way: {user_phonemes} with the expected way being: {expected_phonemes}."

    for viseme_id, phoneme in viseme_ids:
        input_string += f" User had a mistake with the phoneme {phoneme} which can be pronouced using the following description: {viseme_descriptions[viseme_id]}."

    return input_string

def nl_feedback(sentence, expected_phonemes, user_phonemes, errors):

    user_input = extract_input(sentence, expected_phonemes, user_phonemes, errors)
    history.append({"role": "user", "content": user_input})

    chat_input = tokenizer.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([chat_input], return_tensors="pt").to(model.device)
    output_ids = model.generate(**inputs, max_new_tokens=300)
    output = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    history.append({"role": "assistant", "content": output})

    return output

print(nl_feedback("Anthony likes applie pie", "ænθənilaɪksæpəlpaɪ", "æmθənilaɪksæpəlpaɪ", "m"))

