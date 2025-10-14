import re
import ssl
from collections import Counter

import nltk

# Fix SSL certificate issue on macOS
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab')
    except:
        print("Warning: Could not download punkt_tab. Please run download_nltk_data_ssl_fix.py")

try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    try:
        nltk.download('averaged_perceptron_tagger_eng')
    except:
        print("Warning: Could not download averaged_perceptron_tagger_eng. Please run download_nltk_data_ssl_fix.py")

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords')
    except:
        print("Warning: Could not download stopwords. Please run download_nltk_data_ssl_fix.py")

from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords


class TextProcessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def extract_keywords(self, text: str, n: int = 3) -> list[str]:
        """
        Extract the n most frequent nouns from the text.
        
        Args:
            text: The input text
            n: Number of keywords to extract (default: 3)
        
        Returns:
            List of n most frequent nouns
        """
        # Clean and tokenize text
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        tokens = word_tokenize(text)

        # Get POS tags
        tagged = pos_tag(tokens)

        # Extract nouns (NN, NNS, NNP, NNPS)
        nouns = [word for word, tag in tagged
                 if tag in ['NN', 'NNS', 'NNP', 'NNPS']
                 and word not in self.stop_words
                 and len(word) > 2]

        # Count frequencies
        noun_freq = Counter(nouns)

        # Get top n most common nouns
        most_common = noun_freq.most_common(n)

        # Return just the words, not the counts
        return [word for word, count in most_common]

    def calculate_confidence_score(self, text: str, summary: str, topics: list) -> int:
        """
        Calculate a naive confidence score based on text characteristics.
        
        Args:
            text: Original text
            summary: Generated summary
            topics: Extracted topics
        
        Returns:
            Confidence score (0-100)
        """
        score = 50  # Base score

        # Adjust based on text length
        word_count = len(text.split())
        if word_count > 100:
            score += 10
        elif word_count < 20:
            score -= 10

        # Adjust based on summary quality (simple heuristic)
        if len(summary) > 20 and len(summary) < 200:
            score += 10

        # Adjust based on topic relevance (check if topics appear in text)
        text_lower = text.lower()
        topics_found = sum(1 for topic in topics if topic.lower() in text_lower)
        score += topics_found * 5

        # Ensure score is within bounds
        return max(0, min(100, score))
