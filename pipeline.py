from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Tokenizer,Wav2Vec2Processor, Wav2Vec2ForCTC
from phonemizer import phonemize
import Levenshtein as lev
import librosa
import torch
import os

# Specific for my implementation on my personal computer
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = 'C:/Program Files/eSpeak NG/libespeak-ng.dll'

class Pipeline():
    """
    Evaluates speech and returns feedback to
    target pronunciation points that require further work.
    """
    def __init__(self):
        self.model_name = "facebook/wav2vec2-lv-60-espeak-cv-ft"
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
        self.tokenizer = Wav2Vec2Tokenizer.from_pretrained(self.model_name)
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
        similarity = round(distance/max(len(user_phonemes), len(target_phonemes))*100, 2)

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
    
    def get_viseme(self, phoneme):
        """Returns a viseme and a description for a phoneme"""

    def get_feedback(self, phoneme):
        """Returns the corresponding feedback to help understand a phoneme"""
    
    def __call__(self):
        """Makes the whole pipeline run from start to finish"""
        # Step 1. Get the user's phonemes and the reference phonemes
        user_phonemes = self.speech2phonemes('some_arbitrary_audio_path.wav')
        target_phonemes = self.text2phonemes('some_reference_speech')

        # Step 2. Get similarity misalignment indices between attempt and target
        similarity, matches, substitutions, deletions, insertions = self.get_misalignments(user_phonemes, target_phonemes)

        return similarity, matches, substitutions, deletions, insertions