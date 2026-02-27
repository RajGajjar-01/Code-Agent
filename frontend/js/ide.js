/**
 * ide.js — WordPress IDE page logic
 * Depends on: utils.js, api.js (loaded before this file)
 */

'use strict';

/* ─────────────────────────────────────────────────────────────────────────────
   File icon map
───────────────────────────────────────────────────────────────────────────── */
const FILE_ICONS = {
    '.php': '🐘',
    '.js': '📜',
    '.jsx': '📜',
    '.ts': '📘',
    '.tsx': '📘',
    '.css': '🎨',
    '.json': '{}',
    '.html': '🌐',
    '.xml': '📋',
    '.svg': '🖼️',
    '.md': '📝',
};

function getFileIcon(ext) { return FILE_ICONS[ext] || '📄'; }

/* ─────────────────────────────────────────────────────────────────────────────
   Tab Manager
───────────────────────────────────────────────────────────────────────────── */
class TabManager {
    constructor(barEl) {
        this.barEl = barEl;
        this.tabs = new Map();   // path -> { model, savedContent, el }
        this.activePath = null;
        this.onSwitch = null;        // (path) => void
        this.onNoTabs = null;        // () => void
    }

    has(path) { return this.tabs.has(path); }
    get(path) { return this.tabs.get(path); }

    open(path, content, language, model) {
        if (this.tabs.has(path)) { this.activate(path); return; }

        const name = path.split('/').pop();
        const el = document.createElement('div');
        el.className = 'ide-tab';
        el.dataset.path = path;
        el.title = path;
        el.innerHTML = `
            <span class="ide-tab-dot"></span>
            <span class="ide-tab-name">${escapeHtml(name)}</span>
            <button class="ide-tab-close" title="Close">×</button>
        `;
        el.querySelector('.ide-tab-close').addEventListener('click', (e) => { e.stopPropagation(); this.close(path); });
        el.addEventListener('click', () => this.activate(path));
        this.barEl.appendChild(el);

        this.tabs.set(path, { model, savedContent: content, el });
        this.activate(path);
    }

    activate(path) {
        if (!this.tabs.has(path)) return;
        this.activePath = path;
        this.tabs.forEach((t, p) => t.el.classList.toggle('active', p === path));
        if (this.onSwitch) this.onSwitch(path);
    }

    close(path, force = false) {
        const tab = this.tabs.get(path);
        if (!tab) return;
        if (!force && tab.model.getValue() !== tab.savedContent) {
            if (!confirm(`Discard unsaved changes to "${path.split('/').pop()}"?`)) return;
        }
        tab.model.dispose();
        tab.el.remove();
        this.tabs.delete(path);
        if (this.activePath === path) {
            const next = this.tabs.keys().next().value;
            if (next) this.activate(next);
            else { this.activePath = null; if (this.onNoTabs) this.onNoTabs(); }
        }
    }

    markDirty(path) { this.tabs.get(path)?.el.classList.add('unsaved'); }

    markSaved(path, content) {
        const tab = this.tabs.get(path);
        if (!tab) return;
        tab.savedContent = content;
        tab.el.classList.remove('unsaved');
    }

    currentContent() {
        const tab = this.tabs.get(this.activePath);
        return tab ? tab.model.getValue() : null;
    }

    isSaved(path) {
        const tab = this.tabs.get(path);
        return tab ? tab.model.getValue() === tab.savedContent : true;
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   File Tree
───────────────────────────────────────────────────────────────────────────── */
class FileTree {
    constructor(containerEl, onFileOpen, onCreateRequest) {
        this.container = containerEl;
        this.onFileOpen = onFileOpen;
        this.onCreateRequest = onCreateRequest;
        this.expanded = new Set();
        this.activePath = null;
    }

    async load(dir) {
        this.container.innerHTML = `<div style="padding:16px;color:hsl(var(--muted-foreground));font-size:.82rem;">Loading…</div>`;
        const { data, error } = await IdeAPI.getTree(dir);
        if (error) {
            this.container.innerHTML = `<div style="padding:16px;color:hsl(var(--destructive));font-size:.82rem;">${escapeHtml(error)}</div>`;
            return;
        }
        this.container.innerHTML = '';
        if (data.tree?.children?.length) {
            this._render(data.tree.children, this.container, 0);
        }
    }

    _render(nodes, parent, depth) {
        for (const node of nodes) {
            const isDir = node.type === 'directory';
            const isOpen = this.expanded.has(node.path);

            const row = document.createElement('div');
            row.className = `tree-row${this.activePath === node.path ? ' active' : ''}`;
            row.style.setProperty('--depth', depth);
            row.title = node.path;

            row.innerHTML = `
                <span class="tree-chevron">${isDir ? (isOpen ? '▼' : '▶') : ''}</span>
                <span class="tree-icon">${isDir ? '📁' : getFileIcon(node.extension)}</span>
                <span class="tree-name">${escapeHtml(node.name)}</span>
                ${isDir ? `
                <div class="tree-actions">
                    <button class="tree-action-btn" data-action="file"   title="New File">+</button>
                    <button class="tree-action-btn" data-action="folder" title="New Folder">📂</button>
                </div>` : ''}
            `;

            // Action buttons (create file / folder)
            row.querySelectorAll('.tree-action-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.onCreateRequest(node.path, btn.dataset.action === 'file' ? 'file' : 'directory');
                });
            });

            // Row click
            row.addEventListener('click', (e) => {
                if (e.target.closest('.tree-action-btn')) return;
                if (isDir) {
                    if (this.expanded.has(node.path)) this.expanded.delete(node.path);
                    else this.expanded.add(node.path);
                    // Re-render from current root
                    const active = document.querySelector('.root-btn.active');
                    if (active) document.querySelector('.root-btn.active').click();
                } else {
                    this.setActive(node.path);
                    this.onFileOpen(node.path);
                }
            });

            parent.appendChild(row);

            // Render children inline if expanded
            if (isDir && isOpen && node.children?.length) {
                this._render(node.children, parent, depth + 1);
            }
        }
    }

    setActive(path) {
        this.activePath = path;
        this.container.querySelectorAll('.tree-row.active').forEach(r => r.classList.remove('active'));
        this.container.querySelectorAll('.tree-row').forEach(r => {
            if (r.title === path) r.classList.add('active');
        });
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   Toast
───────────────────────────────────────────────────────────────────────────── */
class Toast {
    constructor(containerId) { this.container = document.getElementById(containerId); }

    show(msg, isError = false) {
        const el = document.createElement('div');
        el.className = `toast${isError ? ' toast-error' : ''}`;
        el.textContent = msg;
        this.container.appendChild(el);
        setTimeout(() => el.remove(), isError ? 5000 : 2500);
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   Create Modal
───────────────────────────────────────────────────────────────────────────── */
class CreateModal {
    constructor(overlayId, onSubmit) {
        this.overlay = document.getElementById(overlayId);
        this.titleEl = this.overlay.querySelector('h3');
        this.input = document.getElementById('ide-modal-input');
        this.onSubmit = onSubmit;
        this.state = null;

        document.getElementById('ide-modal-cancel').addEventListener('click', () => this.hide());
        document.getElementById('ide-modal-submit').addEventListener('click', () => this._submit());
        this.input.addEventListener('keydown', (e) => { if (e.key === 'Enter') this._submit(); });
        this.overlay.addEventListener('click', (e) => { if (e.target === this.overlay) this.hide(); });
    }

    show(parentPath, type) {
        this.state = { parentPath, type };
        this.titleEl.textContent = `Create New ${type === 'file' ? 'File' : 'Folder'}`;
        this.input.placeholder = type === 'file' ? 'style.css' : 'new-folder';
        this.input.value = '';
        this.overlay.classList.add('visible');
        setTimeout(() => this.input.focus(), 50);
    }

    hide() { this.overlay.classList.remove('visible'); }

    async _submit() {
        const name = this.input.value.trim();
        if (!name) return;
        await this.onSubmit(this.state.parentPath, name, this.state.type);
        this.hide();
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   IDEApp — Main Orchestrator
───────────────────────────────────────────────────────────────────────────── */
class IDEApp {
    constructor() {
        this.monacoEditor = null;
        this.tabs = new TabManager(document.getElementById('ide-tabs-bar'));
        this.toast = new Toast('ide-toast-container');
        this.tree = new FileTree(
            document.getElementById('file-tree-container'),
            (path) => this._openFile(path),
            (parent, type) => this.modal.show(parent, type)
        );
        this.modal = new CreateModal('ide-modal-overlay', (...args) => this._handleCreate(...args));
        this.currentRoot = null;
    }

    async init() {
        await this._initMonaco();
        this._bindUI();
        await this._loadRoots();
    }

    /* Monaco init */
    _initMonaco() {
        return new Promise(resolve => {
            require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
            require(['vs/editor/editor.main'], () => {
                this.monacoEditor = monaco.editor.create(
                    document.getElementById('ide-editor-container'),
                    {
                        theme: 'vs-light',
                        fontFamily: "'Fira Code', 'Cascadia Code', monospace",
                        fontSize: 14,
                        automaticLayout: true,
                        minimap: { enabled: true },
                        wordWrap: 'off',
                        bracketPairColorization: { enabled: true },
                        suggest: { showWords: true },
                        formatOnPaste: true,
                        scrollBeyondLastLine: false,
                        padding: { top: 12 },
                        smoothScrolling: true,
                        cursorBlinking: 'smooth',
                    }
                );

                this.monacoEditor.onDidChangeModelContent(() => {
                    if (this.tabs.activePath) this.tabs.markDirty(this.tabs.activePath);
                });

                resolve();
            });
        });
    }

    /* UI bindings */
    _bindUI() {
        // Save button
        document.getElementById('ide-save-btn').addEventListener('click', () => this._saveActive());

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); this._saveActive(); }
        });

        // Word wrap toggle
        const wrapBtn = document.getElementById('ide-wrap-btn');
        wrapBtn.addEventListener('click', () => {
            const current = this.monacoEditor.getOption(monaco.editor.EditorOption.wordWrap);
            const next = current === 'off' ? 'on' : 'off';
            this.monacoEditor.updateOptions({ wordWrap: next });
            wrapBtn.textContent = `Wrap: ${next === 'on' ? 'On' : 'Off'}`;
        });

        // Always-visible New File / New Folder buttons in sidebar
        document.getElementById('ide-new-file-btn').addEventListener('click', () => {
            if (!this.currentRoot) { this.toast.show('Select a root directory first', false); return; }
            this.modal.show(this.currentRoot, 'file');
        });
        document.getElementById('ide-new-folder-btn').addEventListener('click', () => {
            if (!this.currentRoot) { this.toast.show('Select a root directory first', false); return; }
            this.modal.show(this.currentRoot, 'directory');
        });

        // Tab manager callbacks
        this.tabs.onSwitch = (path) => {
            const tab = this.tabs.get(path);
            if (!tab) return;
            const welcome = document.getElementById('ide-welcome');
            if (welcome) welcome.style.display = 'none';
            this.monacoEditor.setModel(tab.model);
            document.getElementById('ide-file-info').textContent = path;
            this.tree.setActive(path);
        };
        this.tabs.onNoTabs = () => {
            this.monacoEditor.setModel(null);
            document.getElementById('ide-file-info').textContent = '';
            const welcome = document.getElementById('ide-welcome');
            if (welcome) welcome.style.display = 'flex';
        };
    }

    /* Load roots */
    async _loadRoots() {
        const { data, error } = await IdeAPI.getRoots();
        if (error) { this.toast.show(error, true); return; }

        const grid = document.getElementById('ide-root-grid');
        grid.innerHTML = '';
        const ICONS = { Themes: '🎨', Plugins: '🔌', 'Must-Use Plugins': '⚡' };

        data.roots.forEach((root, i) => {
            const btn = document.createElement('button');
            btn.className = `root-btn${i === 0 ? ' active' : ''}`;
            btn.textContent = `${ICONS[root.name] || '📂'} ${root.name}`;
            btn.addEventListener('click', () => {
                document.querySelectorAll('.root-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentRoot = root.path;
                this.tree.load(root.path);
            });
            grid.appendChild(btn);
            if (i === 0) { this.currentRoot = root.path; this.tree.load(root.path); }
        });
    }

    /* Open a file */
    async _openFile(path) {
        if (this.tabs.has(path)) { this.tabs.activate(path); return; }

        const { data, error } = await IdeAPI.readFile(path);
        if (error) { this.toast.show(`Failed to open: ${error}`, true); return; }

        const tabSize = (data.language === 'json' || data.language === 'css') ? 2 : 4;
        const model = monaco.editor.createModel(data.content, data.language);
        model.updateOptions({ tabSize });
        this.tabs.open(path, data.content, data.language, model);
    }

    /* Save active file */
    async _saveActive() {
        const path = this.tabs.activePath;
        if (!path) { this.toast.show('No file open', false); return; }

        const content = this.tabs.currentContent();
        const { error } = await IdeAPI.writeFile(path, content);
        if (error) { this.toast.show(`Save failed — ${error}`, true); return; }

        this.tabs.markSaved(path, content);
        this.toast.show('Saved ✓');
    }

    /* Handle create file/folder */
    async _handleCreate(parentPath, name, type) {
        const { error } = await IdeAPI.createNode(parentPath, name, type);
        if (error) { this.toast.show(error, true); return; }
        this.toast.show(`Created: ${name}`);
        // Refresh tree
        if (this.currentRoot) this.tree.load(this.currentRoot);
    }

    _makeWelcome() {
        const el = document.createElement('div');
        el.id = 'ide-welcome';
        el.innerHTML = `
            <div style="opacity:.2;margin-bottom:16px;">
                <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
            </div>
            <h2>WordPress Code Editor</h2>
            <p>Select a file from the sidebar to start editing.</p>
            <p>Press <kbd>Ctrl+S</kbd> to save.</p>
        `;
        return el;
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
   Boot
───────────────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => new IDEApp().init());
