const API_BASE = '';

// --- State ---
const state = {
    messages: [],
    chatId: null,
    isLoading: false,
    driveConnected: false,
    driveBreadcrumbs: [{ id: 'root', name: 'My Drive' }],
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
    // Google Drive elements
    driveToggleBtn: document.getElementById('driveToggleBtn'),
    drivePanel: document.getElementById('drivePanel'),
    driveCloseBtn: document.getElementById('driveCloseBtn'),
    driveConnectSection: document.getElementById('driveConnectSection'),
    driveConnectBtn: document.getElementById('driveConnectBtn'),
    driveUserSection: document.getElementById('driveUserSection'),
    driveUserAvatar: document.getElementById('driveUserAvatar'),
    driveUserName: document.getElementById('driveUserName'),
    driveUserEmail: document.getElementById('driveUserEmail'),
    driveDisconnectBtn: document.getElementById('driveDisconnectBtn'),
    driveBreadcrumbs: document.getElementById('driveBreadcrumbs'),
    driveFileList: document.getElementById('driveFileList'),
    driveLoading: document.getElementById('driveLoading'),
};

// --- Initialize ---
function init() {
    bindEvents();
    loadChatHistory();
    checkGoogleAuthStatus();
    handleOAuthRedirect();
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

    // Google Drive
    els.driveToggleBtn.addEventListener('click', toggleDriveSidebar);
    els.driveCloseBtn.addEventListener('click', toggleDriveSidebar);
    els.driveConnectBtn.addEventListener('click', connectGoogleDrive);
    els.driveDisconnectBtn.addEventListener('click', disconnectGoogleDrive);
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


// ============================================
//   GOOGLE DRIVE INTEGRATION
// ============================================

function toggleDriveSidebar() {
    const isCollapsed = els.drivePanel.classList.toggle('collapsed');
    els.driveToggleBtn.classList.toggle('active', !isCollapsed);
}

function handleOAuthRedirect() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('google_auth') === 'success') {
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        // Open the drive panel and refresh status
        els.drivePanel.classList.remove('collapsed');
        els.driveToggleBtn.classList.add('active');
        checkGoogleAuthStatus();
    }
}

async function checkGoogleAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/status`);
        if (!response.ok) return;
        const data = await response.json();

        state.driveConnected = data.connected;

        if (data.connected) {
            showDriveConnected(data);
        } else {
            showDriveDisconnected();
        }
    } catch (e) {
        // Silently fail — server may not be running yet
        console.log('Auth status check failed:', e.message);
    }
}

function connectGoogleDrive() {
    // Redirect to backend OAuth login endpoint
    window.location.href = `${API_BASE}/api/auth/login`;
}

async function disconnectGoogleDrive() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/disconnect`, { method: 'POST' });
        if (response.ok) {
            state.driveConnected = false;
            showDriveDisconnected();
        }
    } catch (e) {
        console.error('Disconnect failed:', e);
    }
}

function showDriveConnected(data) {
    els.driveConnectSection.classList.add('hidden');
    els.driveUserSection.classList.remove('hidden');
    els.driveBreadcrumbs.classList.remove('hidden');
    els.driveFileList.classList.remove('hidden');

    if (data.picture) {
        els.driveUserAvatar.src = data.picture;
        els.driveUserAvatar.style.display = 'block';
    } else {
        els.driveUserAvatar.style.display = 'none';
    }
    els.driveUserName.textContent = data.name || 'Google User';
    els.driveUserEmail.textContent = data.email || '';

    // Load root folder
    state.driveBreadcrumbs = [{ id: 'root', name: 'My Drive' }];
    loadDriveFolder('root');
}

function showDriveDisconnected() {
    els.driveConnectSection.classList.remove('hidden');
    els.driveUserSection.classList.add('hidden');
    els.driveBreadcrumbs.classList.add('hidden');
    els.driveFileList.classList.add('hidden');
    els.driveLoading.classList.add('hidden');
}

async function loadDriveFolder(folderId) {
    els.driveLoading.classList.remove('hidden');
    els.driveFileList.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/drive/folders?parent_id=${encodeURIComponent(folderId)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();

        els.driveLoading.classList.add('hidden');
        els.driveFileList.classList.remove('hidden');

        renderBreadcrumbs();
        renderDriveItems(data.items);
    } catch (e) {
        els.driveLoading.classList.add('hidden');
        els.driveFileList.classList.remove('hidden');
        els.driveFileList.innerHTML = `
            <div style="padding: 20px; text-align: center; color: hsl(var(--muted-foreground)); font-size: 0.82rem;">
                Failed to load files. ${escapeHtml(e.message)}
            </div>
        `;
    }
}

function renderBreadcrumbs() {
    els.driveBreadcrumbs.innerHTML = state.driveBreadcrumbs.map((crumb, i) => {
        const isLast = i === state.driveBreadcrumbs.length - 1;
        const separator = i > 0 ? '<span class="breadcrumb-separator">/</span>' : '';
        return `${separator}<span class="breadcrumb-item" data-id="${crumb.id}" onclick="navigateToBreadcrumb(${i})">${escapeHtml(crumb.name)}</span>`;
    }).join('');
}

function navigateToBreadcrumb(index) {
    if (index === state.driveBreadcrumbs.length - 1) return; // Already here
    state.driveBreadcrumbs = state.driveBreadcrumbs.slice(0, index + 1);
    const folderId = state.driveBreadcrumbs[index].id;
    loadDriveFolder(folderId);
}
window.navigateToBreadcrumb = navigateToBreadcrumb;

function renderDriveItems(items) {
    if (!items || items.length === 0) {
        els.driveFileList.innerHTML = `
            <div style="padding: 30px; text-align: center; color: hsl(var(--muted-foreground)); font-size: 0.82rem;">
                This folder is empty
            </div>
        `;
        return;
    }

    const FOLDER_MIME = 'application/vnd.google-apps.folder';

    els.driveFileList.innerHTML = items.map(item => {
        const isFolder = item.mime_type === FOLDER_MIME;
        const iconClass = isFolder ? 'folder' : 'file';
        const icon = isFolder
            ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>`
            : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>`;

        const meta = item.modified_time
            ? new Date(item.modified_time).toLocaleDateString()
            : '';

        return `
            <div class="drive-file-item" data-id="${item.id}" data-name="${escapeHtml(item.name)}" data-mime="${item.mime_type}" onclick="onDriveItemClick(this)">
                <div class="drive-file-icon ${iconClass}">${icon}</div>
                <div class="drive-file-info">
                    <span class="drive-file-name">${escapeHtml(item.name)}</span>
                    <span class="drive-file-meta">${meta}</span>
                </div>
            </div>
        `;
    }).join('');
}

function onDriveItemClick(el) {
    const id = el.dataset.id;
    const name = el.dataset.name;
    const mime = el.dataset.mime;

    if (mime === 'application/vnd.google-apps.folder') {
        state.driveBreadcrumbs.push({ id, name });
        loadDriveFolder(id);
    } else if (el.querySelector('[data-webviewlink]')) {
        // Open file in new tab if web view link available
        window.open(el.querySelector('[data-webviewlink]').dataset.webviewlink, '_blank');
    }
}
window.onDriveItemClick = onDriveItemClick;
