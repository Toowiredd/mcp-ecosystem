#!/usr/bin/env python3

import json
import logging
import re
import spacy
import difflib
import unicodedata
from typing import Dict, List, Any, Tuple
import enchant
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedCommunicationInterceptor:
    def __init__(self, model_path='en_core_web_lg'):
        """
        Initialize the communication interceptor.
        """
        try:
            self.nlp = spacy.load(model_path)
        except Exception as e:
            logger.error(f"Failed to load SpaCy model: {e}")
            raise

        # Spelling correction dictionary
        self.spelling_corrections = {
            'u': 'you', 'tryna': 'trying to', 'yknow': 'you know',
            'ur': 'your', 'thats': "that's", 'thingy': 'thing',
            'ned': 'need', 'implemnt': 'implement', 
            'commuication': 'communication', 'systm': 'system', 
            'undrstands': 'understands', 'adhd': 'ADHD',
            'devlop': 'develop', 'algorythms': 'algorithms',
            'framwork': 'framework', 'integratin': 'integrating'
        }

        # Contraction mapping
        self.contractions = {
            "wanna": "want to",
            "don't": "do not",
            "can't": "cannot",
            "i'm": "i am",
            "it's": "it is",
            "he's": "he is",
            "she's": "she is",
            "they're": "they are",
            "we're": "we are",
            "you're": "you are",
        }
        self.enchant_dict = enchant.Dict("en_US")

    def preprocess_text(self, text: str) -> str:
        """Normalize, clean, expand contractions, and remove filler words."""
        text = unicodedata.normalize('NFKD', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Expand contractions
        words = text.split()
        expanded_words = [self.contractions.get(word.lower(), word) for word in words]
        text = ' '.join(expanded_words)

        # Remove filler words
        filler_words = ["uh", "um", "like", "you know", "kinda", "sort of", "basically", "actually", "literally"]
        text = re.sub(r'\b(?:' + '|'.join(re.escape(w) for w in filler_words) + r')\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def transform_communication(self, input_text: str) -> str:
        """
        Spelling correction and communication transformation.
        """
        input_text = self.preprocess_text(input_text)
        doc = self.nlp(input_text)
        corrected_tokens = []
        self.num_corrections = 0
        self.original_words = []

        for token in doc:
            self.original_words.append(token.text)
            lower_word = token.text.lower()

            if token.is_alpha:
                # Apply predefined spelling corrections
                corrected_word = self.spelling_corrections.get(lower_word)

                # Fallback spell check
                if corrected_word is None:
                    if not self.enchant_dict.check(token.text):
                        suggestions = self.enchant_dict.suggest(token.text)
                        if suggestions:
                            corrected_word = suggestions[0]
                            self.num_corrections += 1
                        else:
                            corrected_word = token.text
                    else:
                        corrected_word = token.text
                elif corrected_word != token.text:
                    self.num_corrections += 1

                corrected_tokens.append(corrected_word)
            else:
                corrected_tokens.append(token.text)
        
        return ' '.join(corrected_tokens)

    def _calculate_changed_percentage(self) -> float:
        """Calculates the percentage of words that were changed."""
        if not self.original_words:
            return 0.0

        original_counts = Counter(self.original_words)
        corrected_text = self.transform_communication(' '.join(self.original_words))
        corrected_counts = Counter(corrected_text.split())

        changed_count = 0
        for word, orig_count in original_counts.items():
            corrected_count = corrected_counts.get(word, 0)
            changed_count += abs(orig_count - corrected_count)

        total_original_words = len(self.original_words)
        return (changed_count / total_original_words) * 100 if total_original_words > 0 else 0.0

    def extract_intent(self, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """
        Extract basic intent and key linguistic features.
        """
        # Find root verb
        root_verb = None
        for token in doc:
            if token.dep_ == "ROOT":
                root_verb = token.lemma_
                break
        if root_verb is None:
            root_verb = next((token.lemma_ for token in doc if token.pos_ == 'VERB'), 'Unknown')

        # Extract key concepts with linguistic details
        key_concepts = [
            {
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'dep': token.dep_,
                'show_lemma': token.lemma_.lower() != token.text.lower() and len(token.lemma_) > 1
            } for token in doc
            if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'PROPN']
        ]

        return {
            'primary_action': root_verb,
            'key_concepts': key_concepts
        }

    def generate_insights(self, input_text: str) -> str:
        """
        Generate comprehensive communication insights.
        """
        try:
            corrected_text = self.transform_communication(input_text)
            doc = self.nlp(corrected_text)
            intent_analysis = self.extract_intent(doc)

            # Generate communication recommendations
            recommendations = []
            if any(word in input_text.lower() for word in ["uh", "um", "like", "you know"]):
                recommendations.append("Try to reduce the use of filler words.")

            insights = {
                'communication_profile': {
                    'original_input': input_text,
                    'corrected_input': corrected_text,
                    'intent_analysis': intent_analysis
                },
                'recommendations': {
                    'communication_strategy': ' '.join(recommendations) if recommendations else "Provide clear, structured communication"
                },
                'performance_metrics': {
                    'num_corrections': self.num_corrections,
                    'changed_word_percentage': self._calculate_changed_percentage()
                }
            }
            return json.dumps(insights)

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return json.dumps({
                'communication_profile': {
                    'original_input': input_text,
                    'corrected_input': input_text,
                    'intent_analysis': {}
                },
                'recommendations': {'communication_strategy': 'Default'},
                'performance_metrics': {'num_corrections': 0, 'changed_word_percentage': 0.0},
                'error': str(e)
            })

def main():
    interceptor = AdvancedCommunicationInterceptor()

    # Use the input text as the test case
    input_text = input().strip()
    
    insights_json = interceptor.generate_insights(input_text)
    insights = json.loads(insights_json)
    
    # Output ONLY the transformed prompt
    print(insights['communication_profile']['corrected_input'])
    
    # Save full insights to a separate JSON file
    with open('/tmp/communication_insights.json', 'w') as f:
        json.dump(insights, f, indent=4)

if __name__ == '__main__':
    main()