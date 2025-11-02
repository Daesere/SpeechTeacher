import ollama
import os

# --------------------------
# IPA → Viseme mapping
# --------------------------
ipa_to_viseme = {
    '_': 0, ' ': 0,
    'æ': 1, 'a': 1, 'ə': 1, 'ʌ': 1, 'ɐ': 1,
    'ɑ': 2, 'ɑː': 2, 'ɒ': 2,
    'ɔ': 3, 'ɔː': 3,
    'e': 4, 'eɪ': 4, 'ɛ': 4,
    'ɜ': 5, 'ɜː': 5, 'ɝ': 5, 'ɚ': 5,
    'j': 6, 'i': 6, 'iː': 6, 'ɪ': 6, 'ɨ': 6,
    'w': 7, 'u': 7, 'uː': 7, 'ʊ': 7,
    'o': 8, 'oʊ': 8, 'əʊ': 8,
    'aʊ': 9,
    'ɔɪ': 10,
    'aɪ': 11,
    'h': 12, 'ɦ': 12,
    'r': 13, 'ɹ': 13, 'ɾ': 13,
    'l': 14, 'ɫ': 14,
    's': 15, 'z': 15,
    'ʃ': 16, 'tʃ': 16, 'dʒ': 16, 'ʒ': 16,
    'θ': 17, 'ð': 17,
    'f': 18, 'v': 18,
    'd': 19, 't': 19, 'n': 19,
    'k': 20, 'g': 20, 'ŋ': 20, 'ɡ': 20,
    'p': 21, 'b': 21, 'm': 21
}

# --------------------------
# Viseme descriptions
# --------------------------
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

# --------------------------
# Viseme identification
# --------------------------
def viseme_identifier(diffs):
    ids = []
    
    for diff in diffs:
        one = ipa_to_viseme.get(diff, 0)
        
        ids.append((one, diff))
        
    return ids

def viseme_path_identifier(diffs):
    ids = viseme_identifier(diffs)
    paths = []
    for id, phoneme in ids:
        path = f"./viseme_feedback/visemes/viseme-id-{id}.jpg"
        paths.append(path)
    return paths

# --------------------------
# Prompt construction
# --------------------------
def extract_input(sentence, expected_phonemes, user_phonemes, errors):
    viseme_ids = viseme_identifier(errors)
    input_string = (
        f"The user pronounced the sentence \"{sentence}\" as: {user_phonemes}.\n"
        f"The correct pronunciation should be: {expected_phonemes}.\n"
    )
    for viseme_id, phoneme in viseme_ids:
        input_string += (
            f"\n- Mistake: {phoneme}\n"
            f"  → Description: {viseme_descriptions[viseme_id]}"
        )
    input_string += "\n\nExplain what went wrong and give advice to correct it. Add at the end some potential sentences (1 to 10 words) they could try."
    return input_string

# --------------------------
# Ollama setup
# --------------------------
history = [{"role": "system", "content": "You are a phonetics coach helping learners improve pronunciation. Strictly follow the instructions please."}]

def nl_feedback(sentence, expected_phonemes, user_phonemes, errors):
    global history
    user_input = extract_input(sentence, expected_phonemes, user_phonemes, errors)
    history.append({"role": "user", "content": user_input})

    response = ollama.chat(
        model="qwen3:8b",  # replace with your Ollama model name
        messages=history,
        think=False,
        options={"temperature": 0.0}
    )
    print(response)

    assistant_text = response['message']['content']
    history.append({"role": "assistant", "content": assistant_text})

    # Keep history short
    if len(history) > 10:
        history = history[:1] + history[-9:]

    return assistant_text
