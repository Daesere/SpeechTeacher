from PIL import Image
import time
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

diffs = "gtʃb"

def viseme_identifier(diffs):
    ids = []
    i = 0


    while i < len(diffs):
        one = ipa_to_viseme.get(diffs[i], None)
        two = ipa_to_viseme.get(diffs[i:i+2], None) if i + 1 < len(diffs) else None
        image_id = 0
        if two is not None:
            image_id = two
            i += 1
            ids.append((image_id, two))
        elif one is not None:
            image_id = one
            ids.append((image_id, one))s

        i += 1
        
    return ids

def viseme_path_identifier(diffs):
    ids = viseme_identifier(diffs)
    paths = []
    for id, phoneme in ids:
        path = f"./viseme_feedback/visemes/viseme-id-{id}.jpg"
        paths.append(path)
    return paths