/**
 * api.js — All HTTP communication with the FastAPI backend
 * Used by: chat.js, ide.js
 *
 * All methods return { data, error } — they never throw.
 */

'use strict';

const API_BASE = '';

/* ─────────────────────────────────────────────────────────────────────────────
   Internal fetch wrapper
───────────────────────────────────────────────────────────────────────────── */
async function _apiFetch(url, options = {}) {
    try {
        const res = await fetch(API_BASE + url, options);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return { data: null, error: data.detail || res.statusText };
        return { data, error: null };
    } catch (err) {
        return { data: null, error: err.message };
    }
}

function _json(method, url, body) {
    return _apiFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}


/* ─────────────────────────────────────────────────────────────────────────────
   Chat API
───────────────────────────────────────────────────────────────────────────── */
const ChatAPI = {
    /** POST /api/chat */
    send(message, conversationId, userEmail) {
        return _json('POST', '/api/chat', {
            message,
            conversation_id: conversationId || null,
            user_email: userEmail,
        });
    },

    /** GET /api/conversations */
    listConversations(userEmail, limit = 40) {
        return _apiFetch(`/api/conversations?user_email=${encodeURIComponent(userEmail)}&limit=${limit}`);
    },

    /** GET /api/conversations/:id */
    getConversation(id) {
        return _apiFetch(`/api/conversations/${id}`);
    },

    /** DELETE /api/conversations/:id */
    deleteConversation(id) {
        return _apiFetch(`/api/conversations/${id}`, { method: 'DELETE' });
    },
};


/* ─────────────────────────────────────────────────────────────────────────────
   Auth / Google Drive API
───────────────────────────────────────────────────────────────────────────── */
const AuthAPI = {
    /** GET /api/auth/status */
    getStatus() { return _apiFetch('/api/auth/status'); },

    /** POST /api/auth/disconnect */
    disconnect() { return _apiFetch('/api/auth/disconnect', { method: 'POST' }); },

    /** Redirect to /api/auth/login */
    startLogin() { window.location.href = `${API_BASE}/api/auth/login`; },
};

const DriveAPI = {
    /** GET /api/drive/folders */
    listFolder(parentId = 'root', pageToken = null) {
        const qs = pageToken ? `&page_token=${pageToken}` : '';
        return _apiFetch(`/api/drive/folders?parent_id=${encodeURIComponent(parentId)}${qs}`);
    },
};


/* ─────────────────────────────────────────────────────────────────────────────
   IDE Filesystem API
───────────────────────────────────────────────────────────────────────────── */
const IdeAPI = {
    /** GET /api/ide/tree/roots */
    getRoots() { return _apiFetch('/api/ide/tree/roots'); },

    /** GET /api/ide/tree?dir=... */
    getTree(dir) { return _apiFetch(`/api/ide/tree?dir=${encodeURIComponent(dir)}`); },

    /** GET /api/ide/file?path=... */
    readFile(path) { return _apiFetch(`/api/ide/file?path=${encodeURIComponent(path)}`); },

    /** POST /api/ide/file */
    writeFile(path, content) { return _json('POST', '/api/ide/file', { path, content }); },

    /** POST /api/ide/create */
    createNode(parent_path, name, type) {
        return _json('POST', '/api/ide/create', { parent_path, name, type });
    },
};
