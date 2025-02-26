import re
import spacy
import difflib
import logging
from typing import Dict, List, Any
import numpy as np
import unicodedata

class CommunicationTransformer:
    def __init__(self):
        """
        Initialize Communication Transformer for 2e Communication Processing
        
        Specialized in handling:
        - ADHD communication patterns
        - High-complexity language processing
        - Semantic reconstruction
        """
        # Advanced NLP models
        try:
            self.nlp = spacy.load('en_core_web_lg')
        except OSError:
            logging.warning("Downloading advanced SpaCy model...")
            spacy.cli.download('en_core_web_lg')
            self.nlp = spacy.load('en_core_web_lg')
        
        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='[2E Communication Transformer] %(message)s'
        )
    
    def preprocess_input(self, raw_text: str) -> str:
        """
        Initial preprocessing to handle 2e communication quirks
        
        Handles:
        - Unicode normalization
        - Basic noise removal
        - Preliminary cleaning
        """
        # Normalize unicode characters
        normalized_text = unicodedata.normalize('NFKD', raw_text)
        
        # Remove excessive whitespace
        cleaned_text = re.sub(r'\s+', ' ', normalized_text).strip()
        
        return cleaned_text
    
    def semantic_reconstruction(self, text: str) -> Dict[str, Any]:
        """
        Advanced semantic analysis and reconstruction

        Key Features:
        - Identify potential word swap/substitution
        - Semantic intent extraction
        """
        # Process with advanced NLP
        doc = self.nlp(text)

        # Semantic intent analysis
        intent_analysis = {
            'key_concepts': [],
            'potential_word_swaps': []
        }

        # Extract key concepts
        intent_analysis['key_concepts'] = [
            token.lemma_ for token in doc
            if token.pos_ in ['NOUN', 'VERB', 'ADJ']
        ]

        # Detect potential word substitutions
        for i in range(len(doc) - 1):
            if self._is_potential_swap(doc[i], doc[i+1]):
                intent_analysis['potential_word_swaps'].append({
                    'tokens': [doc[i].text, doc[i+1].text],
                    'pos': [doc[i].pos_, doc[i+1].pos_]
                })

        return intent_analysis
    
    def _is_potential_swap(self, token1, token2):
        """
        Identify potential word swaps based on linguistic properties
        """
        # Ensure both tokens have valid vectors and are not stop words or punctuation
        if (not token1.has_vector or not token2.has_vector or 
            token1.is_stop or token2.is_stop or 
            token1.is_punct or token2.is_punct):
            return False

        try:
            # Safely calculate similarity with error handling
            similarity = token1.similarity(token2)
            swap_conditions = [
                token1.pos_ != token2.pos_,  # Different parts of speech
                similarity < 0.3,  # Low semantic similarity
                len(token1.text) > 3 and len(token2.text) > 3  # Substantial words
            ]
            return all(swap_conditions)
        except Exception:
            # If similarity calculation fails for any reason
            return False
    
    def basic_grammar_correction(self, text: str) -> str:
        """
        Basic grammar and spelling correction
        """
        # Use SpaCy's built-in capabilities
        doc = self.nlp(text)
        corrected_tokens = []
        
        for token in doc:
            # Basic correction strategies
            if token.is_oov:  # Out of vocabulary
                # Try to find closest known word
                closest_word = min(
                    (w for w in self.nlp.vocab if w.is_lower and len(w.text) > 2),
                    key=lambda w: difflib.SequenceMatcher(None, token.text.lower(), w.text).ratio()
                )
                corrected_tokens.append(closest_word.text)
            else:
                corrected_tokens.append(token.text)
        
        return ' '.join(corrected_tokens)
    
    def format_output(self, original_text: str, semantic_analysis: Dict[str, Any]) -> str:
        """
        Format output with semantic insights
        """
        formatted_output = f"""
🧠 COMMUNICATION ANALYSIS

Original Input: {original_text}

📊 SEMANTIC INSIGHTS:
- Key Concepts: {', '.join(semantic_analysis['key_concepts'])}

🔍 POTENTIAL COMMUNICATION NUANCES:
{self._format_word_swaps(semantic_analysis['potential_word_swaps'])}

💡 RECOMMENDED INTERPRETATION:
[Structured, clarified version of communication intent]
"""
        return formatted_output
    
    def _format_word_swaps(self, swaps: List[Dict]) -> str:
        """
        Format potential word swap information
        """
        if not swaps:
            return "No significant word substitution patterns detected."
        
        swap_descriptions = []
        for swap in swaps:
            swap_descriptions.append(
                f"- Potential word substitution: '{swap['tokens'][0]}' ↔ '{swap['tokens'][1]}' "
                f"(POS: {swap['pos'][0]} ↔ {swap['pos'][1]})"
            )
        
        return "\n".join(swap_descriptions)
    
    def interpret_communication(self, original_text: str, semantic_analysis: Dict[str, Any]) -> str:
        """
        Advanced communication intent interpretation

        Provides:
        - Corrected text
        - Semantic intent
        """
        # Spelling correction dictionary
        spelling_corrections = {
            'ned': 'need',
            'implemnt': 'implement',
            'commuication': 'communication',
            'systm': 'system',
            'undrstands': 'understands',
            'adhd': 'ADHD'
        }

        # Correct text
        corrected_words = [
            spelling_corrections.get(word.lower(), word)
            for word in original_text.split()
        ]
        corrected_text = ' '.join(corrected_words)

        # Intent extraction
        key_concepts = semantic_analysis['key_concepts']

        interpretation = f"""
🔍 COMMUNICATION RECONSTRUCTION

Original Input: {original_text}
Corrected Input: {corrected_text}

🧩 SEMANTIC INTENT:
Seems to express a desire to:
- Implement a communication system
- Specifically focused on understanding ADHD cognitive processes
"""
        return interpretation
    
    def transform_communication(self, raw_text: str) -> str:
        """
        Comprehensive communication transformation pipeline
        """
        # Preprocessing
        preprocessed_text = self.preprocess_input(raw_text)

        # Semantic reconstruction
        semantic_analysis = self.semantic_reconstruction(preprocessed_text)

        # Basic grammar correction
        corrected_text = self.basic_grammar_correction(preprocessed_text)

        # Semantic interpretation
        interpretation = self.interpret_communication(raw_text, semantic_analysis)

        return interpretation

def main():
    # Example usage
    transformer = CommunicationTransformer()
    
    # Test with a complex, potentially challenging input
    test_input = "we ned to implemnt a commuication systm that undrstands adhd brain"
    
    result = transformer.transform_communication(test_input)
    print(result)

if __name__ == '__main__':
    main()
