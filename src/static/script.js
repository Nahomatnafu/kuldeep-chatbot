// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const questionForm = document.getElementById('questionForm');
const questionInput = document.getElementById('questionInput');
const sendButton = document.getElementById('sendButton');
const sendIcon = document.getElementById('sendIcon');
const loadingIcon = document.getElementById('loadingIcon');
const clearButton = document.getElementById('clearButton');

// Generate a unique session ID for this browser tab
const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

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
        // Send request to backend with session ID
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                session_id: sessionId
            }),
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

// Clear conversation history
if (clearButton) {
    clearButton.addEventListener('click', async () => {
        if (!confirm('Clear conversation history? This will start a fresh conversation.')) {
            return;
        }

        try {
            const response = await fetch('/api/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: sessionId }),
            });

            const data = await response.json();

            if (response.ok) {
                // Clear chat UI (keep only welcome message)
                const welcomeMessage = chatContainer.querySelector('.bot-message');
                chatContainer.innerHTML = '';
                if (welcomeMessage) {
                    chatContainer.appendChild(welcomeMessage);
                }

                // Add system message
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message bot-message';
                messageDiv.innerHTML = `
                    <div class="message-content">
                        <p><strong>🔄 Conversation cleared!</strong> Starting fresh.</p>
                    </div>
                `;
                chatContainer.appendChild(messageDiv);
                scrollToBottom();
            } else {
                throw new Error(data.error || 'Failed to clear conversation');
            }
        } catch (error) {
            console.error('Error clearing conversation:', error);
            addErrorMessage('Failed to clear conversation: ' + error.message);
        }
    });
}

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

