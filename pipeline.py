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
        # self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
        # self.tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(self.model_name)
        # self.processor = Wav2Vec2Processor.from_pretrained(self.model_name, feature_extractor=self.feature_extractor, tokenizer=self.tokenizer)
        # self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)

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
        # Step 1. Get the user's phonemes and the reference phonemes
        similarity = 75
    
        # Simulated phonemes (actual IPA representations)
        target_phonemes = "ˈænθəni laɪks ˈæpəl paɪ"
        user_phonemes = "ˈænθəni laks ˈæpəl paɪ"
        
        # Simulated error locations
        substituted = [{
            'viseme_path': 'visemes/viseme-id-2.jpg',  # Example path
            'start_index': 10,
            'end_index': 11,
            'type': 'substitution',
            'correct': 'laɪks'
        }]
        
        inserted = []  # No insertions in this example
        
        deleted = []   # No deletions in this example
        
        
        feedback = """Here's my feedback on your pronunciation:

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

        Keep practicing these sounds, and you'll see improvement quickly! Would you like to try again?"""
        
        return similarity, substituted, inserted, deleted, feedback, target_phonemes
        user_phonemes = self.speech2phonemes(audio_path)
        target_phonemes = self.text2phonemes(reference_text)

        # Step 2. Get similarity misalignment indices between attempt and target
        similarity, matches, substitutions, deletions, insertions = self.get_misalignments(user_phonemes, target_phonemes)
        
        # 3. Bundle errors
        substituted = [
            {
                'viseme_path': viseme_path_identifier(target_phonemes[deletion[0][0]:deletion[0][1]]),
                'start_index': int(deletion[0][0]),
                'end_index': int(deletion[0][1]),
                'type': 'substitution',
                'correct': reference_text[deletion[0][0]:deletion[0][0]]
            }

            for deletion in deletions
        ]

        inserted = [
            {
                'start_index': int(insertion[0][0]),
                'end_index': int(insertion[0][1]),
                'type': 'insertion',
            }

            for insertion in insertions
        ]

        deleted = [
            {
                'viseme_path': viseme_path_identifier(target_phonemes[deletion[0][0]:deletion[0][1]]),
                'index': int(deletion[0][0]),
                'type': 'deletion',
                'correct': reference_text[deletion[0][0]:deletion[0][1]]
            }

            for deletion in deletions
        ]

        errors = [target_phonemes[deletion[0][0]:deletion[0][1]] for deletion in deletions] + [target_phonemes[sub[0][0]:sub[0][1]] for sub in substitutions]
        feedback = nl_feedback(reference_text, target_phonemes, user_phonemes, errors)
        
        # Add some formatting to make the feedback stand out
        conversation = f"**Feedback**: {feedback}"

        return similarity, substituted, inserted, deleted, feedback
    
listener = Listener()

if __name__ == "__main__":
    audio_path = 'test.wav' # Audio of reference_speech
    reference_speech = 'Anthony likes apple pie'
    output = listener(reference_speech, audio_path)

    print(output)