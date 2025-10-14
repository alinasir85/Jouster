#!/usr/bin/env python3
"""Download required NLTK data with SSL fix for macOS"""

import ssl

import nltk

print("Setting up SSL context and downloading NLTK data...")

# Create unverified SSL context as a workaround
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download the required data
print("Downloading punkt_tab...")
nltk.download('punkt_tab')

print("Downloading averaged_perceptron_tagger_eng...")
nltk.download('averaged_perceptron_tagger_eng')

print("Downloading stopwords...")
nltk.download('stopwords')

print("\nNLTK data download complete!")
print("You can now run the application.")
