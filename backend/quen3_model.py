from transformers import AutoModelForCausalLM, AutoTokenizer
import os

ipa_to_viseme = {
    # Viseme 0: Silence
    '_': 0,
    ' ': 0,
    
    # Viseme 1: ae, ax, ah
    'æ': 1,
    'a': 1,
    'ə': 1,
    'ʌ': 1,
    'ɐ': 1,
    
    # Viseme 2: aa
    'ɑ': 2,
    'ɑː': 2,
    'ɒ': 2,
    
    # Viseme 3: ao
    'ɔ': 3,
    'ɔː': 3,
    
    # Viseme 4: ey
    'e': 4,
    'eɪ': 4,
    'ɛ': 4,
    
    # Viseme 5: er
    'ɜ': 5,
    'ɜː': 5,
    'ɝ': 5,
    'ɚ': 5,
    
    # Viseme 6: y, iy, ih, ix
    'j': 6,
    'i': 6,
    'iː': 6,
    'ɪ': 6,
    'ɨ': 6,
    
    # Viseme 7: w, uw
    'w': 7,
    'u': 7,
    'uː': 7,
    'ʊ': 7,
    
    # Viseme 8: ow
    'o': 8,
    'oʊ': 8,
    'əʊ': 8,
    
    # Viseme 9: aw
    'aʊ': 9,
    
    # Viseme 10: oy
    'ɔɪ': 10,
    
    # Viseme 11: ay
    'aɪ': 11,
    
    # Viseme 12: h
    'h': 12,
    'ɦ': 12,
    
    # Viseme 13: r
    'r': 13,
    'ɹ': 13,
    'ɾ': 13,
    
    # Viseme 14: l
    'l': 14,
    'ɫ': 14,
    
    # Viseme 15: s, z
    's': 15,
    'z': 15,
    
    # Viseme 16: sh, ch, jh, zh
    'ʃ': 16,
    'tʃ': 16,
    'dʒ': 16,
    'ʒ': 16,
    
    # Viseme 17: th, dh
    'θ': 17,
    'ð': 17,
    
    # Viseme 18: f, v
    'f': 18,
    'v': 18,
    
    # Viseme 19: d, t, n
    'd': 19,
    't': 19,
    'n': 19,
    
    # Viseme 20: k, g, ng
    'k': 20,
    'g': 20,
    'ŋ': 20,
    'ɡ': 20,
    
    # Viseme 21: p, b, m
    'p': 21,
    'b': 21,
    'm': 21,
}

def viseme_identifier(diffs):
    ids = []

    for diff in diffs:
        one = ipa_to_viseme.get(diff, None)
        image_id = 0
        if one is not None:
            image_id = one
            ids.append((image_id, one))
        
    return ids

def viseme_path_identifier(diffs):
    ids = viseme_identifier(diffs)
    paths = []
    for id, phoneme in ids:
        path = f"./viseme_feedback/visemes/viseme-id-{id}.jpg"
        paths.append(path)
    return paths




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

model_name = "Qwen/Qwen3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)

from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    device_map="auto" # Automatically infers device mapping
)

model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

base_history = "You are a phonetics coach helping learners improve pronunciation."

history = [
    {"role": "system", "content": base_history}
]


def extract_input(sentence, expected_phonemes, user_phonemes, errors):
    
    viseme_ids: tuple[str, int] = viseme_identifier(errors)
    
    input_string = f"The user pronounced the sentence \"{sentence}\" this way: {user_phonemes} with the expected way being: {expected_phonemes}."

    input_string = (
    f"The user pronounced the sentence \"{sentence}\" as: {user_phonemes}.\n"
    f"The correct pronunciation should be: {expected_phonemes}.\n"
    )

    for viseme_id, phoneme in viseme_ids:
        input_string += (
            f"\n- Mistake: {phoneme}\n"
            f"  → Description: {viseme_descriptions[viseme_id]}"
        )
    return input_string

def nl_feedback(sentence, expected_phonemes, user_phonemes, errors):
    global history
    user_input = extract_input(sentence, expected_phonemes, user_phonemes, errors)
    history.append({"role": "user", "content": user_input})

    chat_input = tokenizer.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([chat_input], return_tensors="pt").to(model.device)
    output_ids = model.generate(**inputs, max_new_tokens=1024)
    output = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    history.append({"role": "assistant", "content": output})
    if len(history) > 10:
        history = history[:1] + history[-9:]
    return output

print(nl_feedback("Anthony likes apple pie", "ænθənilaɪksæpəlpaɪ", "æmθənilaɪksæpəlpaɪ", ["m"]))

