from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2CTCTokenizer,Wav2Vec2Processor, Wav2Vec2ForCTC
from phonemizer import phonemize
from phonemizer.separator import Separator
import Levenshtein as lev
import librosa
import torch
import os

# Modules that we developed
from backend.quen3_model import nl_feedback, viseme_path_identifier

# Specific for my implementation on my personal computer
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = 'C:/Program Files/eSpeak NG/libespeak-ng.dll'

class Listener():
    """
    Evaluates speech and returns feedback to
    target pronunciation points that require further work.
    """
    def __init__(self):
        self.model_name = "facebook/wav2vec2-lv-60-espeak-cv-ft"
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
        self.tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(self.model_name)
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_name, feature_extractor=self.feature_extractor, tokenizer=self.tokenizer)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)

    def speech2phonemes(self, audio_path):
        """Transforms user audio into IPA phonemes for evaluation"""
        # Load and normalize the user's audio
        speech, sr = librosa.load(audio_path, sr=16_000, mono=True)
        speech = librosa.util.normalize(speech)

        # Process input and generate logits
        inputs = self.processor(speech, sampling_rate=16_000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = self.model(inputs.input_values).logits

        # Decode the logits into phonemes and return
        predicted_ids = torch.argmax(logits, dim=-1)
        phonemes = self.processor.batch_decode(predicted_ids)[0]
        
        return phonemes
    
    def text2phonemes(self, text):
        """Converts text into IPA phonemes using eSpeak-NG"""
        phonemes = phonemize(text, language='en-us').replace(' ', '')
        return phonemes
    
    def get_misalignments(self, user_phonemes, target_phonemes):
        """Evaluates alignment between two phoneme sequences"""
        # Get the Levenshtein alignment codes
        opcodes = lev.opcodes(target_phonemes, user_phonemes)
        # Compute a percentage similarity based on Levenshtein distance
        distance = lev.distance(target_phonemes, user_phonemes)
        similarity = round(100 - distance/max(len(user_phonemes), len(target_phonemes))*100)

        matches = []
        substitutions = []
        deletions = []
        insertions = []
                
        # Extract matches and various kinds of errors
        for op, ref_start, ref_end, user_start, user_end in opcodes:
            # Encode as reference indices and attempt indices
            indices = ((ref_start, ref_end), (user_start, user_end))

            if op == 'equal':
                matches.append(indices)
            elif op == 'replace':
                substitutions.append(indices)
            elif op == 'delete':
                deletions.append(indices)
            elif op == 'insert':
                insertions.append(indices)

        return similarity, matches, substitutions, deletions, insertions
    

    def get_feedback(self, phoneme):
        """Returns the corresponding feedback to help understand a phoneme"""
    
    def __call__(self, reference_text, audio_path):
        """Makes the whole pipeline run from start to finish"""

        """
        # Step 1. Get the user's phonemes and the reference phonemes
        similarity = 75
    
        # Simulated phonemes (actual IPA representations)
        target_phonemes = "ˈænθəni laɪks ˈæpəl paɪ"
        user_phonemes = "ˈænθəni laks ˈæpəl paɪ"
        
        # Simulated error locations
        substituted = [{
            'viseme_path': 'frontend/visemes/viseme-id-2.jpg',  # Example path
            'start_index': 10,
            'end_index': 11,
            'type': 'substitution',
            'correct': 'laɪks'
        }]
        
        inserted = []  # No insertions in this example
        
        deleted = []   # No deletions in this example
        
        
        feedback = Here's my feedback on your pronunciation:

        1. Overall Score: 75% - Good effort, but there's room for improvement!

        2. Specific Observations:
        • The word "likes" needs attention - you said "laks" instead of "laɪks"
        • Your pronunciation of "Anthony" and "apple pie" was excellent
        • The rhythm and timing of your speech is natural

        3. Tips for Improvement:
        • For "likes": Make the "aɪ" sound by starting with "ah" and gliding to "ee"
        • Try saying: "l-eye-k-s" slowly, then speed it up
        • Practice this sound in other words like: "time", "ride", "life"

        4. What You Did Well:
        • Clear pronunciation of consonants
        • Good word stress patterns
        • Natural speaking pace

        Here's my feedback on your pronunciation:

        1. Overall Score: 75% - Good effort, but there's room for improvement!

        2. Specific Observations:
        • The word "likes" needs attention - you said "laks" instead of "laɪks"
        • Your pronunciation of "Anthony" and "apple pie" was excellent
        • The rhythm and timing of your speech is natural

        3. Tips for Improvement:
        • For "likes": Make the "aɪ" sound by starting with "ah" and gliding to "ee"
        • Try saying: "l-eye-k-s" slowly, then speed it up
        • Practice this sound in other words like: "time", "ride", "life"

        4. What You Did Well:
        • Clear pronunciation of consonants
        • Good word stress patterns
        • Natural speaking pace

        Keep practicing these sounds, and you'll see improvement quickly! Would you like to try again?
        
        return similarity, substituted, inserted, deleted, feedback, target_phonemes
        """

        # Generate phonemes from audio and reference text
        user_phonemes = self.speech2phonemes(audio_path)
        target_phonemes = self.text2phonemes(reference_text)

        # Step 2. Get similarity misalignment indices between attempt and target
        similarity, matches, substitutions, deletions, insertions = self.get_misalignments(user_phonemes, target_phonemes)

        # IMPORTANT NOTE: Error indices are packed as [((ref_start, ref_end), (att_start, att_end))]

        # Bundle up substitutions: if the viseme identifier returns multiple paths,
        # emit one correction entry per viseme so the frontend can render each separately.
        substituted = []
        for substitution in substitutions:
            ref_start, ref_end = substitution[0][0], substitution[0][1]
            viseme_paths = viseme_path_identifier(target_phonemes[ref_start:ref_end])
            # If viseme_paths is a list, create one correction per path
            if isinstance(viseme_paths, (list, tuple)) and len(viseme_paths) > 0:
                for vp in viseme_paths:
                    substituted.append({
                        'viseme_path': vp,
                        'start_index': ref_start,
                        'end_index': ref_end,
                        'type': 'substitution',
                        'correct': target_phonemes[ref_start:ref_end]
                    })
            else:
                # fallback, keep single entry with whatever was returned
                substituted.append({
                    'viseme_path': viseme_paths,
                    'start_index': ref_start,
                    'end_index': ref_end,
                    'type': 'substitution',
                    'correct': target_phonemes[ref_start:ref_end]
                })

        # Bundle up my insertions (no viseme images expected)
        inserted = []
        for insertion in insertions:
            ref_start, ref_end = insertion[0][0], insertion[0][1]
            inserted.append({
                'start_index': ref_start,
                'end_index': ref_end,
                'type': 'insertion',
            })

        # Bundle up deletions similarly to substitutions (may have visemes)
        deleted = []
        for deletion in deletions:
            ref_start, ref_end = deletion[0][0], deletion[0][1]
            viseme_paths = viseme_path_identifier(target_phonemes[ref_start:ref_end])
            if isinstance(viseme_paths, (list, tuple)) and len(viseme_paths) > 0:
                for vp in viseme_paths:
                    deleted.append({
                        'viseme_path': vp,
                        'start_index': ref_start,
                        'end_index': ref_end,
                        'type': 'deletion',
                        'correct': target_phonemes[ref_start:ref_end]
                    })
            else:
                deleted.append({
                    'viseme_path': viseme_paths,
                    'start_index': ref_start,
                    'end_index': ref_end,
                    'type': 'deletion',
                    'correct': target_phonemes[ref_start:ref_end]
                })

        errors = [target_phonemes[deletion[0][0]:deletion[0][1]] for deletion in deletions] + [target_phonemes[sub[0][0]:sub[0][1]] for sub in substitutions]
        feedback = nl_feedback(reference_text, target_phonemes, user_phonemes, errors)

        # Target these variables to return
        return similarity, substituted, inserted, deleted, feedback, target_phonemes, user_phonemes
    
listener = Listener()

if __name__ == "__main__":
    audio_path = 'test.wav' # Audio of reference_speech
    reference_speech = 'Anthony likes apple pie'
    output = listener(reference_speech, audio_path)

    print(output)