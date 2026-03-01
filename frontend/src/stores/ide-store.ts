import { create } from 'zustand'
import { ideApi } from '@/lib/axios'
import type { Root, TabData, TreeNode } from '@/types'

interface IdeStore {
    roots: Root[]
    currentRoot: string | null
    treeData: TreeNode[]
    expandedPaths: Set<string>
    openTabs: Map<string, TabData>
    activePath: string | null
    isTreeLoading: boolean

    loadRoots: () => Promise<void>
    loadTree: (dir: string) => Promise<void>
    toggleExpanded: (path: string) => void
    openFile: (path: string) => Promise<void>
    activateTab: (path: string) => void
    closeTab: (path: string) => void
    markDirty: (path: string) => void
    saveFile: (path: string, content: string) => Promise<{ error?: string }>
    createNode: (parent: string, name: string, type: string) => Promise<{ error?: string }>
    setCurrentRoot: (root: string) => void
}

export const useIdeStore = create<IdeStore>((set, get) => ({
    roots: [],
    currentRoot: null,
    treeData: [],
    expandedPaths: new Set<string>(),
    openTabs: new Map<string, TabData>(),
    activePath: null,
    isTreeLoading: false,

    loadRoots: async () => {
        try {
            const { data } = await ideApi.getRoots()
            const roots = data.roots
            set({ roots })
            if (roots.length > 0) {
                set({ currentRoot: roots[0].path })
                get().loadTree(roots[0].path)
            }
        } catch (e) {
            console.error('Failed to load roots:', e)
        }
    },

    loadTree: async (dir) => {
        set({ isTreeLoading: true })
        try {
            const { data } = await ideApi.getTree(dir)
            set({ treeData: data.tree?.children || [], isTreeLoading: false })
        } catch (e) {
            console.error('Failed to load tree:', e)
            set({ treeData: [], isTreeLoading: false })
        }
    },

    setCurrentRoot: (root) => {
        set({ currentRoot: root })
        get().loadTree(root)
    },

    toggleExpanded: (path) => {
        set((s) => {
            const next = new Set(s.expandedPaths)
            if (next.has(path)) next.delete(path)
            else next.add(path)
            return { expandedPaths: next }
        })
    },

    openFile: async (path) => {
        const { openTabs } = get()
        if (openTabs.has(path)) {
            set({ activePath: path })
            return
        }

        try {
            const { data } = await ideApi.readFile(path)
            set((s) => {
                const next = new Map(s.openTabs)
                next.set(path, {
                    content: data.content,
                    language: data.language,
                    savedContent: data.content,
                    isDirty: false,
                })
                return { openTabs: next, activePath: path }
            })
        } catch (e) {
            console.error('Failed to open file:', e)
        }
    },

    activateTab: (path) => set({ activePath: path }),

    closeTab: (path) => {
        set((s) => {
            const next = new Map(s.openTabs)
            next.delete(path)
            let newActive = s.activePath
            if (s.activePath === path) {
                const keys = Array.from(next.keys())
                newActive = keys.length > 0 ? keys[keys.length - 1] : null
            }
            return { openTabs: next, activePath: newActive }
        })
    },

    markDirty: (path) => {
        set((s) => {
            const next = new Map(s.openTabs)
            const tab = next.get(path)
            if (tab) next.set(path, { ...tab, isDirty: true })
            return { openTabs: next }
        })
    },

    saveFile: async (path, content) => {
        try {
            await ideApi.writeFile(path, content)
            set((s) => {
                const next = new Map(s.openTabs)
                const tab = next.get(path)
                if (tab) next.set(path, { ...tab, savedContent: content, isDirty: false })
                return { openTabs: next }
            })
            return {}
        } catch (e) {
            return { error: e instanceof Error ? e.message : 'Save failed' }
        }
    },

    createNode: async (parent, name, type) => {
        // Validation: Check for empty name
        if (!name || name.trim().length === 0) {
            return { error: 'File name cannot be empty' }
        }

        // Validation: Check for invalid characters
        const invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        const foundInvalidChars = invalidChars.filter(char => name.includes(char))
        if (foundInvalidChars.length > 0) {
            return { error: `File name contains invalid characters: ${foundInvalidChars.join(', ')}` }
        }

        // Validation: Check name length (max 255 characters, common filesystem limit)
        if (name.length > 255) {
            return { error: 'File name exceeds maximum length (255 characters)' }
        }

        try {
            await ideApi.createNode(parent, name, type)
            const { currentRoot } = get()
            if (currentRoot) get().loadTree(currentRoot)
            return {}
        } catch (e) {
            return { error: e instanceof Error ? e.message : 'Create failed' }
        }
    },
}))
