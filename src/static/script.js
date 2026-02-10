// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const questionForm = document.getElementById('questionForm');
const questionInput = document.getElementById('questionInput');
const sendButton = document.getElementById('sendButton');
const sendIcon = document.getElementById('sendIcon');
const loadingIcon = document.getElementById('loadingIcon');

// Add user message to chat
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add bot message to chat
function addBotMessage(answer, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                <div class="sources-title">📚 Sources (${sources.length} chunks)</div>
                ${sources.map(source => `
                    <div class="source-item">
                        <div class="source-file">[${source.id}] ${source.file} (page ${source.page})</div>
                        <div class="source-snippet">"${escapeHtml(source.snippet)}"</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(answer)}</p>
            ${sourcesHtml}
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add error message
function addErrorMessage(error) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message error-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p><strong>❌ Error:</strong> ${escapeHtml(error)}</p>
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Set loading state
function setLoading(isLoading) {
    sendButton.disabled = isLoading;
    questionInput.disabled = isLoading;
    
    if (isLoading) {
        sendIcon.style.display = 'none';
        loadingIcon.style.display = 'inline';
    } else {
        sendIcon.style.display = 'inline';
        loadingIcon.style.display = 'none';
    }
}

// Handle form submission
questionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = questionInput.value.trim();
    if (!question) return;
    
    // Add user message
    addUserMessage(question);
    
    // Clear input
    questionInput.value = '';
    
    // Set loading state
    setLoading(true);
    
    try {
        // Send request to backend
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong');
        }
        
        // Add bot response
        addBotMessage(data.answer, data.sources);
        
    } catch (error) {
        console.error('Error:', error);
        addErrorMessage(error.message);
    } finally {
        setLoading(false);
        questionInput.focus();
    }
});

// Focus input on load
window.addEventListener('load', () => {
    questionInput.focus();
});

// Check health on load
fetch('/api/health')
    .then(response => response.json())
    .then(data => {
        console.log('Health check:', data);
    })
    .catch(error => {
        console.error('Health check failed:', error);
    });

