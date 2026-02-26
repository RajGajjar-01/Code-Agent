const API_BASE = '';

// --- State ---
const state = {
    messages: [],
    chatId: null,
    isLoading: false,
};

// --- DOM Elements ---
const els = {
    sidebar: document.getElementById('sidebar'),
    headerToggleBtn: document.getElementById('headerToggleBtn'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    newChatBtn: document.getElementById('newChatBtn'),
    chatHistory: document.getElementById('chatHistory'),
    chatTitle: document.getElementById('chatTitle'),
    messagesContainer: document.getElementById('messagesContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesList: document.getElementById('messagesList'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    toolCallModal: document.getElementById('toolCallModal'),
    toolCallDetails: document.getElementById('toolCallDetails'),
    modalClose: document.getElementById('modalClose'),
};

// --- Initialize ---
function init() {
    bindEvents();
    loadChatHistory();
}

// --- Event Bindings ---
function bindEvents() {
    // Sidebar
    els.headerToggleBtn.addEventListener('click', toggleSidebar);
    els.mobileMenuBtn.addEventListener('click', toggleSidebar);

    // New Chat
    els.newChatBtn.addEventListener('click', startNewChat);

    // Send message
    els.sendBtn.addEventListener('click', sendMessage);
    els.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    els.messageInput.addEventListener('input', () => {
        els.messageInput.style.height = 'auto';
        els.messageInput.style.height = Math.min(els.messageInput.scrollHeight, 160) + 'px';
        els.sendBtn.disabled = !els.messageInput.value.trim();
    });

    // Suggestion cards
    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.dataset.prompt;
            els.messageInput.value = prompt;
            els.sendBtn.disabled = false;
            els.messageInput.focus();
        });
    });

    // Modal
    els.modalClose.addEventListener('click', closeModal);
    els.toolCallModal.addEventListener('click', (e) => {
        if (e.target === els.toolCallModal) closeModal();
    });
}

// --- Sidebar ---
function toggleSidebar() {
    els.sidebar.classList.toggle('collapsed');
}

// --- Chat Management ---
function startNewChat() {
    state.messages = [];
    state.chatId = Date.now().toString(36);
    els.messagesList.innerHTML = '';
    els.welcomeScreen.classList.remove('hidden');
    els.chatTitle.textContent = 'WordPress Agent';
    els.messageInput.focus();
}

function loadChatHistory() {
    const saved = localStorage.getItem('wp_agent_chats');
    if (saved) {
        const chats = JSON.parse(saved);
        renderChatHistory(chats);
    }
}

function saveChatToHistory(title) {
    const saved = localStorage.getItem('wp_agent_chats') || '[]';
    const chats = JSON.parse(saved);
    const existing = chats.findIndex(c => c.id === state.chatId);

    if (existing >= 0) {
        chats[existing].title = title;
        chats[existing].updatedAt = new Date().toISOString();
    } else {
        chats.unshift({
            id: state.chatId,
            title: title,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        });
    }

    // Keep last 20 chats
    localStorage.setItem('wp_agent_chats', JSON.stringify(chats.slice(0, 20)));
    renderChatHistory(chats.slice(0, 20));
}

function renderChatHistory(chats) {
    els.chatHistory.innerHTML = chats.map(chat => `
        <div class="chat-history-item ${chat.id === state.chatId ? 'active' : ''}" data-id="${chat.id}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>${escapeHtml(chat.title)}</span>
        </div>
    `).join('');
}

// --- Message Handling ---
async function sendMessage() {
    const text = els.messageInput.value.trim();
    if (!text || state.isLoading) return;

    // Init chat if needed
    if (!state.chatId) {
        state.chatId = Date.now().toString(36);
    }

    // Hide welcome screen
    els.welcomeScreen.classList.add('hidden');

    // Add user message
    addMessage('user', text);
    els.messageInput.value = '';
    els.messageInput.style.height = 'auto';
    els.sendBtn.disabled = true;

    // Save to history
    const chatTitle = text.slice(0, 50) + (text.length > 50 ? '...' : '');
    saveChatToHistory(chatTitle);
    els.chatTitle.textContent = chatTitle;

    // Show typing indicator
    const typingEl = showTypingIndicator();

    state.isLoading = true;

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                chat_id: state.chatId,
                history: state.messages.slice(-10), // Send last 10 messages for context
            }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // Remove typing indicator
        typingEl.remove();

        // Handle tool calls if present
        if (data.tool_calls && data.tool_calls.length > 0) {
            for (const tc of data.tool_calls) {
                addToolCallBadge(tc);
            }
        }

        // Add assistant response
        if (data.response) {
            addMessage('assistant', data.response);
        }

    } catch (error) {
        typingEl.remove();
        addMessage('assistant', `⚠️ Error: ${error.message}. Make sure the backend server is running at \`${API_BASE}\`.`);
    } finally {
        state.isLoading = false;
    }
}

function addMessage(role, content) {
    state.messages.push({ role, content });

    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const avatarContent = role === 'user' ? 'You' :
        `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`;

    messageEl.innerHTML = `
        <div class="message-inner">
            <div class="message-avatar">${avatarContent}</div>
            <div class="message-content">
                <div class="message-role">${role === 'user' ? 'You' : 'WP Agent'}</div>
                <div class="message-text">${formatMarkdown(content)}</div>
            </div>
        </div>
    `;

    els.messagesList.appendChild(messageEl);
    scrollToBottom();
}

function addToolCallBadge(toolCall) {
    const badge = document.createElement('div');
    badge.className = 'message assistant';
    badge.innerHTML = `
        <div class="message-inner">
            <div class="message-avatar" style="visibility: hidden;">—</div>
            <div class="message-content">
                <div class="tool-call-badge ${toolCall.status === 'success' ? 'success' : ''}" onclick="showToolCallDetails(${JSON.stringify(toolCall).replace(/"/g, '&quot;')})">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                    </svg>
                    <span>Tool: ${escapeHtml(toolCall.name)}</span>
                    ${toolCall.status === 'success' ? '✓' : '⏳'}
                </div>
            </div>
        </div>
    `;
    els.messagesList.appendChild(badge);
    scrollToBottom();
}

function showTypingIndicator() {
    const el = document.createElement('div');
    el.className = 'message assistant';
    el.innerHTML = `
        <div class="message-inner">
            <div class="message-avatar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <div class="message-content">
                <div class="message-role">WP Agent</div>
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    els.messagesList.appendChild(el);
    scrollToBottom();
    return el;
}

// --- Modal ---
function showToolCallDetails(toolCall) {
    els.toolCallDetails.innerHTML = `
        <p><strong>Function:</strong> ${escapeHtml(toolCall.name)}</p>
        <p><strong>Status:</strong> ${toolCall.status || 'pending'}</p>
        <p><strong>Arguments:</strong></p>
        <pre>${JSON.stringify(toolCall.arguments || {}, null, 2)}</pre>
        ${toolCall.result ? `<p><strong>Result:</strong></p><pre>${JSON.stringify(toolCall.result, null, 2)}</pre>` : ''}
    `;
    els.toolCallModal.classList.add('active');
}
// Make it globally accessible for onclick
window.showToolCallDetails = showToolCallDetails;

function closeModal() {
    els.toolCallModal.classList.remove('active');
}

// --- Utilities ---
function scrollToBottom() {
    requestAnimationFrame(() => {
        els.messagesContainer.scrollTop = els.messagesContainer.scrollHeight;
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    // Basic markdown formatting
    return text
        // Code blocks
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Headers
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        // Line breaks to paragraphs
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^(.+)$/s, '<p>$1</p>');
}

// --- Boot ---
document.addEventListener('DOMContentLoaded', init);
