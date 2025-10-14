// API Configuration
const API_BASE_URL = window.location.origin;

// DOM Elements
const textInput = document.getElementById('textInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const loadRecentBtn = document.getElementById('loadRecentBtn');
const currentResult = document.getElementById('currentResult');
const searchResults = document.getElementById('searchResults');
const recentAnalyses = document.getElementById('recentAnalyses');
const loadingSpinner = document.getElementById('loadingSpinner');
const errorToast = document.getElementById('errorToast');

// Event Listeners
analyzeBtn.addEventListener('click', analyzeText);
searchBtn.addEventListener('click', searchAnalyses);
loadRecentBtn.addEventListener('click', loadRecentAnalyses);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchAnalyses();
});

// Analyze Text
async function analyzeText() {
    const text = textInput.value.trim();
    if (!text) {
        showError('Please enter some text to analyze');
        return;
    }

    showLoading(true);
    analyzeBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({text}),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const result = await response.json();
        displayCurrentResult(result);
        textInput.value = '';
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
        analyzeBtn.disabled = false;
    }
}

// Search Analyses
async function searchAnalyses() {
    const topic = searchInput.value.trim();
    if (!topic) {
        showError('Please enter a search term');
        return;
    }

    showLoading(true);
    searchBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/search?topic=${encodeURIComponent(topic)}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Search failed');
        }

        const data = await response.json();
        displaySearchResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
        searchBtn.disabled = false;
    }
}

// Load Recent Analyses
async function loadRecentAnalyses() {
    showLoading(true);
    loadRecentBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/analyses?limit=10`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load analyses');
        }

        const analyses = await response.json();
        displayRecentAnalyses(analyses);
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
        loadRecentBtn.disabled = false;
    }
}

// Display Functions
function displayCurrentResult(result) {
    const content = currentResult.querySelector('.result-content');
    content.innerHTML = formatAnalysisResult(result);
    currentResult.classList.remove('hidden');
}

function displaySearchResults(data) {
    if (data.analyses.length === 0) {
        searchResults.innerHTML = '<p class="no-results">No results found for your search.</p>';
    } else {
        searchResults.innerHTML = `
            <p class="results-count">Found ${data.total_count} result(s) for "${data.search_term}"</p>
            ${data.analyses.map(formatAnalysisResult).join('')}
        `;
    }
    searchResults.classList.remove('hidden');
}

function displayRecentAnalyses(analyses) {
    if (analyses.length === 0) {
        recentAnalyses.innerHTML = '<p class="no-results">No analyses found.</p>';
    } else {
        recentAnalyses.innerHTML = analyses.map(formatAnalysisResult).join('');
    }
    recentAnalyses.classList.remove('hidden');
}

// Format Analysis Result
function formatAnalysisResult(analysis) {
    const date = new Date(analysis.created_at).toLocaleString();
    const title = analysis.title || 'Untitled Analysis';

    return `
        <div class="result-item">
            <div class="result-header">
                <h3 class="result-title">${escapeHtml(title)}</h3>
                <span class="result-date">${date}</span>
            </div>
            
            <p class="result-summary">${escapeHtml(analysis.summary)}</p>
            
            <div class="result-meta">
                <div class="meta-item">
                    <span class="meta-label">Sentiment:</span>
                    <span class="sentiment ${analysis.sentiment}">${analysis.sentiment}</span>
                </div>
                
                <div class="meta-item">
                    <span class="meta-label">Confidence:</span>
                    <div class="confidence">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${analysis.confidence_score}%"></div>
                        </div>
                        <span>${analysis.confidence_score}%</span>
                    </div>
                </div>
            </div>
            
            <div class="result-meta">
                <div class="meta-item">
                    <span class="meta-label">Topics:</span>
                    <div class="tags">
                        ${analysis.topics.map(topic =>
        `<span class="tag topic">${escapeHtml(topic)}</span>`
    ).join('')}
                    </div>
                </div>
            </div>
            
            <div class="result-meta">
                <div class="meta-item">
                    <span class="meta-label">Keywords:</span>
                    <div class="tags">
                        ${analysis.keywords.map(keyword =>
        `<span class="tag keyword">${escapeHtml(keyword)}</span>`
    ).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Utility Functions
function showLoading(show) {
    if (show) {
        loadingSpinner.classList.remove('hidden');
    } else {
        loadingSpinner.classList.add('hidden');
    }
}

function showError(message) {
    const errorMessage = errorToast.querySelector('.error-message');
    errorMessage.textContent = message;
    errorToast.classList.remove('hidden');

    setTimeout(() => {
        errorToast.classList.add('hidden');
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Focus on text input
    textInput.focus();
});
