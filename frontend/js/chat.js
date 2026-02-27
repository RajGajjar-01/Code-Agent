/**
 * chat.js — Main chat page logic
 * Depends on: utils.js, api.js (loaded before this file)
 */

'use strict';

/* ─────────────────────────────────────────────────────────────────────────────
   State
───────────────────────────────────────────────────────────────────────────── */
const state = {
    messages: [],
    conversationId: null,
    userEmail: 'anonymous',
    isLoading: false,
    driveConnected: false,
    driveBreadcrumbs: [{ id: 'root', name: 'My Drive' }],
};

/* ─────────────────────────────────────────────────────────────────────────────
   DOM refs
───────────────────────────────────────────────────────────────────────────── */
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
    // Drive
    driveToggleBtn: document.getElementById('driveToggleBtn'),
    drivePanel: document.getElementById('drivePanel'),
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
    browseFilesBtn: document.getElementById('browseFilesBtn'),
    connectorStatusText: document.getElementById('connectorStatusText'),
};

/* ─────────────────────────────────────────────────────────────────────────────
   Init
───────────────────────────────────────────────────────────────────────────── */
function init() {
    bindEvents();
    loadConversationList();
    checkGoogleAuthStatus();
    handleOAuthRedirect();
}

/* ─────────────────────────────────────────────────────────────────────────────
   Event Bindings
───────────────────────────────────────────────────────────────────────────── */
function bindEvents() {
    els.headerToggleBtn.addEventListener('click', toggleSidebar);
    els.mobileMenuBtn.addEventListener('click', toggleSidebar);
    els.newChatBtn.addEventListener('click', startNewChat);
    els.sendBtn.addEventListener('click', sendMessage);

    els.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    els.messageInput.addEventListener('input', () => {
        els.messageInput.style.height = 'auto';
        els.messageInput.style.height = Math.min(els.messageInput.scrollHeight, 160) + 'px';
        els.sendBtn.disabled = !els.messageInput.value.trim();
    });

    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', () => {
            els.messageInput.value = card.dataset.prompt;
            els.sendBtn.disabled = false;
            els.messageInput.focus();
        });
    });

    els.modalClose.addEventListener('click', closeModal);
    els.toolCallModal.addEventListener('click', (e) => { if (e.target === els.toolCallModal) closeModal(); });

    // Drive
    els.driveToggleBtn.addEventListener('click', toggleDriveSidebar);
    els.driveConnectBtn.addEventListener('click', () => AuthAPI.startLogin());
    els.driveDisconnectBtn.addEventListener('click', disconnectGoogleDrive);
    els.browseFilesBtn.addEventListener('click', () => {
        els.driveFileList.scrollIntoView({ behavior: 'smooth' });
    });
}

/* ─────────────────────────────────────────────────────────────────────────────
   Sidebar
───────────────────────────────────────────────────────────────────────────── */
function toggleSidebar() { els.sidebar.classList.toggle('collapsed'); }

/* ─────────────────────────────────────────────────────────────────────────────
   Chat Management
───────────────────────────────────────────────────────────────────────────── */
function startNewChat() {
    state.messages = [];
    state.conversationId = null;
    els.messagesList.innerHTML = '';
    els.welcomeScreen.classList.remove('hidden');
    els.chatTitle.textContent = 'WordPress Agent';
    els.messageInput.focus();
    document.querySelectorAll('.chat-history-item').forEach(el => el.classList.remove('active'));
}

async function loadConversationList() {
    setHistoryLoading(true);
    try {
        const { data, error } = await ChatAPI.listConversations(state.userEmail);
        if (error) throw new Error(error);
        renderChatHistory(data);
    } catch (e) {
        console.error('Failed to load conversations:', e);
        els.chatHistory.innerHTML = `<div class="history-empty">Could not load history</div>`;
    } finally {
        setHistoryLoading(false);
    }
}

function setHistoryLoading(loading) {
    if (loading) {
        els.chatHistory.innerHTML = `<div class="history-loading"><span></span><span></span><span></span></div>`;
    }
}

function renderChatHistory(conversations) {
    if (!conversations.length) {
        els.chatHistory.innerHTML = `<div class="history-empty">No conversations yet</div>`;
        return;
    }

    els.chatHistory.innerHTML = conversations.map(convo => `
        <div class="chat-history-item ${convo.id === state.conversationId ? 'active' : ''}"
             data-id="${convo.id}"
             title="${escapeHtml(convo.title)}">
            <svg class="chat-history-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span class="chat-history-label">${escapeHtml(convo.title)}</span>
            <button class="chat-delete-btn" data-id="${convo.id}" title="Delete conversation" aria-label="Delete conversation">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
                    <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
                </svg>
            </button>
        </div>
    `).join('');

    els.chatHistory.querySelectorAll('.chat-history-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.chat-delete-btn')) return;
            openConversation(item.dataset.id, item.querySelector('.chat-history-label').textContent);
        });
    });

    els.chatHistory.querySelectorAll('.chat-delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(btn.dataset.id);
        });
    });
}

async function openConversation(conversationId, title) {
    if (state.isLoading) return;

    document.querySelectorAll('.chat-history-item').forEach(el => {
        el.classList.toggle('active', el.dataset.id === conversationId);
    });

    els.welcomeScreen.classList.add('hidden');
    els.chatTitle.textContent = title;
    els.messagesList.innerHTML = `<div class="messages-loading">Loading conversation…</div>`;

    try {
        const { data, error } = await ChatAPI.getConversation(conversationId);
        if (error) throw new Error(error);

        state.conversationId = conversationId;
        state.messages = data.messages || [];

        els.messagesList.innerHTML = '';
        data.messages.forEach(m => addMessageToDOM(m.role, m.content, m.tool_calls));
        scrollToBottom(els.messagesContainer);
    } catch (e) {
        els.messagesList.innerHTML = `<div style="padding:24px;color:hsl(var(--muted-foreground));font-size:.85rem;">Failed to load conversation.</div>`;
        console.error(e);
    }
}

async function deleteConversation(conversationId) {
    try {
        const { error } = await ChatAPI.deleteConversation(conversationId);
        if (error) { console.error('Delete failed:', error); return; }

        if (state.conversationId === conversationId) startNewChat();

        const item = els.chatHistory.querySelector(`[data-id="${conversationId}"]`);
        if (item) {
            item.style.transition = 'all 0.2s ease';
            item.style.opacity = '0';
            item.style.transform = 'translateX(-12px)';
            setTimeout(() => {
                item.remove();
                if (!els.chatHistory.querySelector('.chat-history-item')) {
                    els.chatHistory.innerHTML = `<div class="history-empty">No conversations yet</div>`;
                }
            }, 200);
        }
    } catch (e) {
        console.error('Delete failed:', e);
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   Message Handling
───────────────────────────────────────────────────────────────────────────── */
async function sendMessage() {
    const text = els.messageInput.value.trim();
    if (!text || state.isLoading) return;

    els.welcomeScreen.classList.add('hidden');
    addMessageToDOM('user', text);
    els.messageInput.value = '';
    els.messageInput.style.height = 'auto';
    els.sendBtn.disabled = true;

    if (!state.conversationId) {
        els.chatTitle.textContent = text.slice(0, 50) + (text.length > 50 ? '…' : '');
    }

    const typingEl = showTypingIndicator();
    state.isLoading = true;

    try {
        const { data, error } = await ChatAPI.send(text, state.conversationId, state.userEmail);
        typingEl.remove();
        if (error) throw new Error(error);

        if (data.conversation_id && !state.conversationId) {
            state.conversationId = data.conversation_id;
            await loadConversationList();
            const item = els.chatHistory.querySelector(`[data-id="${state.conversationId}"]`);
            if (item) item.classList.add('active');
        }

        if (data.tool_calls?.length) renderToolCallBadges(data.tool_calls);
        if (data.response) {
            addMessageToDOM('assistant', data.response);
            state.messages.push({ role: 'assistant', content: data.response });
        }
    } catch (err) {
        typingEl.remove();
        addMessageToDOM('assistant', `⚠️ Error: ${err.message}. Make sure the backend is running.`);
    } finally {
        state.isLoading = false;
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   Rendering Helpers
───────────────────────────────────────────────────────────────────────────── */
function addMessageToDOM(role, content, toolCalls = null) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const avatarContent = role === 'user'
        ? 'You'
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`;

    messageEl.innerHTML = `
        <div class="message-inner">
            <div class="message-avatar">${avatarContent}</div>
            <div class="message-content">
                <div class="message-role">${role === 'user' ? 'You' : 'WP Agent'}</div>
                <div class="message-text">${formatMarkdown(content)}</div>
            </div>
        </div>
    `;

    if (toolCalls?.calls?.length) {
        const group = document.createElement('div');
        group.className = 'tool-calls-group';
        toolCalls.calls.forEach(tc => group.appendChild(buildToolCallBadge(tc)));
        messageEl.querySelector('.message-content').appendChild(group);
    }

    els.messagesList.appendChild(messageEl);
    scrollToBottom(els.messagesContainer);
    return messageEl;
}

function buildToolCallBadge(toolCall) {
    const el = document.createElement('div');
    el.className = `tool-call-badge ${toolCall.status === 'success' ? 'success' : ''}`;
    el.setAttribute('onclick', `showToolCallDetails(${JSON.stringify(toolCall).replace(/"/g, '&quot;')})`);
    el.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
        </svg>
        <span>Tool: ${escapeHtml(toolCall.name || toolCall.function || 'tool')}</span>
    `;
    return el;
}

function renderToolCallBadges(toolCalls) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant';
    const inner = document.createElement('div');
    inner.className = 'message-inner';
    inner.innerHTML = `
        <div class="message-avatar" style="visibility:hidden">—</div>
        <div class="message-content"><div class="tool-calls-group"></div></div>
    `;
    const group = inner.querySelector('.tool-calls-group');
    toolCalls.forEach(tc => group.appendChild(buildToolCallBadge(tc)));
    wrapper.appendChild(inner);
    els.messagesList.appendChild(wrapper);
    scrollToBottom(els.messagesContainer);
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
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        </div>
    `;
    els.messagesList.appendChild(el);
    scrollToBottom(els.messagesContainer);
    return el;
}

/* ─────────────────────────────────────────────────────────────────────────────
   Tool Call Modal
───────────────────────────────────────────────────────────────────────────── */
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
window.showToolCallDetails = showToolCallDetails;

function closeModal() { els.toolCallModal.classList.remove('active'); }

/* ─────────────────────────────────────────────────────────────────────────────
   Google Drive / Auth
───────────────────────────────────────────────────────────────────────────── */
function toggleDriveSidebar() {
    const isCollapsed = els.drivePanel.classList.toggle('collapsed');
    els.driveToggleBtn.classList.toggle('active', !isCollapsed);
}

function handleOAuthRedirect() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('google_auth') === 'success') {
        window.history.replaceState({}, document.title, window.location.pathname);
        els.drivePanel.classList.remove('collapsed');
        els.driveToggleBtn.classList.add('active');
        checkGoogleAuthStatus();
    }
}

async function checkGoogleAuthStatus() {
    const { data, error } = await AuthAPI.getStatus();
    if (error) { console.log('Auth status check failed:', error); return; }

    state.driveConnected = data.connected;
    if (data.connected) {
        if (data.email) state.userEmail = data.email;
        showDriveConnected(data);
        loadConversationList();
    } else {
        showDriveDisconnected();
    }
}

async function disconnectGoogleDrive() {
    const { error } = await AuthAPI.disconnect();
    if (!error) {
        state.driveConnected = false;
        state.userEmail = 'anonymous';
        showDriveDisconnected();
    }
}

function showDriveConnected(data) {
    els.driveConnectSection.classList.add('hidden');
    els.driveUserSection.classList.remove('hidden');
    els.driveBreadcrumbs.classList.remove('hidden');
    els.driveFileList.classList.remove('hidden');

    els.driveConnectBtn.classList.add('hidden');
    els.browseFilesBtn.classList.remove('hidden');
    els.driveDisconnectBtn.classList.remove('hidden');

    if (els.connectorStatusText) {
        els.connectorStatusText.textContent = 'Account connected successfully.';
        els.connectorStatusText.style.color = 'var(--success)';
    }

    if (data.picture) { els.driveUserAvatar.src = data.picture; els.driveUserAvatar.style.display = 'block'; }
    else els.driveUserAvatar.style.display = 'none';
    els.driveUserName.textContent = data.name || 'Google User';
    els.driveUserEmail.textContent = data.email || '';

    state.driveBreadcrumbs = [{ id: 'root', name: 'My Drive' }];
    loadDriveFolder('root');
}

function showDriveDisconnected() {
    els.driveConnectSection.classList.remove('hidden');
    els.driveUserSection.classList.add('hidden');
    els.driveBreadcrumbs.classList.add('hidden');
    els.driveFileList.classList.add('hidden');
    els.driveLoading.classList.add('hidden');

    els.driveConnectBtn.classList.remove('hidden');
    els.browseFilesBtn.classList.add('hidden');
    els.driveDisconnectBtn.classList.add('hidden');

    if (els.connectorStatusText) {
        els.connectorStatusText.textContent = 'Connect and access your files.';
        els.connectorStatusText.style.color = '';
    }
}

async function loadDriveFolder(folderId) {
    els.driveLoading.classList.remove('hidden');
    els.driveFileList.classList.add('hidden');

    const { data, error } = await DriveAPI.listFolder(folderId);
    els.driveLoading.classList.add('hidden');
    els.driveFileList.classList.remove('hidden');

    if (error) {
        els.driveFileList.innerHTML = `<div style="padding:20px;text-align:center;color:hsl(var(--muted-foreground));font-size:.82rem;">Failed to load files. ${escapeHtml(error)}</div>`;
        return;
    }

    renderBreadcrumbs();
    renderDriveItems(data.items);
}

function renderBreadcrumbs() {
    els.driveBreadcrumbs.innerHTML = state.driveBreadcrumbs.map((crumb, i) => {
        const sep = i > 0 ? `<span class="breadcrumb-separator">/</span>` : '';
        return `${sep}<span class="breadcrumb-item" data-id="${crumb.id}" onclick="navigateToBreadcrumb(${i})">${escapeHtml(crumb.name)}</span>`;
    }).join('');
}

function navigateToBreadcrumb(index) {
    if (index === state.driveBreadcrumbs.length - 1) return;
    state.driveBreadcrumbs = state.driveBreadcrumbs.slice(0, index + 1);
    loadDriveFolder(state.driveBreadcrumbs[index].id);
}
window.navigateToBreadcrumb = navigateToBreadcrumb;

function renderDriveItems(items) {
    const FOLDER_MIME = 'application/vnd.google-apps.folder';
    if (!items?.length) {
        els.driveFileList.innerHTML = `<div style="padding:30px;text-align:center;color:hsl(var(--muted-foreground));font-size:.82rem;">This folder is empty</div>`;
        return;
    }

    els.driveFileList.innerHTML = items.map(item => {
        const isFolder = item.mime_type === FOLDER_MIME;
        const icon = isFolder
            ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>`
            : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>`;
        const meta = item.modified_time ? new Date(item.modified_time).toLocaleDateString() : '';

        return `
            <div class="drive-file-item" data-id="${item.id}" data-name="${escapeHtml(item.name)}" data-mime="${item.mime_type}" onclick="onDriveItemClick(this)">
                <div class="drive-file-icon ${isFolder ? 'folder' : 'file'}">${icon}</div>
                <div class="drive-file-info">
                    <span class="drive-file-name">${escapeHtml(item.name)}</span>
                    <span class="drive-file-meta">${meta}</span>
                </div>
            </div>
        `;
    }).join('');
}

function onDriveItemClick(el) {
    if (el.dataset.mime === 'application/vnd.google-apps.folder') {
        state.driveBreadcrumbs.push({ id: el.dataset.id, name: el.dataset.name });
        loadDriveFolder(el.dataset.id);
    }
}
window.onDriveItemClick = onDriveItemClick;

/* ─────────────────────────────────────────────────────────────────────────────
   Boot
───────────────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', init);
