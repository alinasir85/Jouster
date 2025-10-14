#!/bin/bash
# Setup script for LLM Knowledge Extractor

echo "Setting up LLM Knowledge Extractor..."

# Create virtual environment with Python 3.12 if available
if command -v python3.12 &> /dev/null; then
    echo "Creating virtual environment with Python 3.12..."
    python3.12 -m venv venv
elif command -v python3.11 &> /dev/null; then
    echo "Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv
else
    echo "Creating virtual environment with default Python 3..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng'); nltk.download('stopwords')"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env and add your OpenAI API key"
fi

echo "Setup complete! Activate the virtual environment with: source venv/bin/activate"
echo "Then run the application with: python main.py"
