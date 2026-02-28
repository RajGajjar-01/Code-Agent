import { create } from 'zustand'
import { chatApi } from '@/lib/axios'
import type { Conversation, Message, ToolCall } from '@/types'

interface ChatStore {
    messages: Message[]
    conversationId: string | null
    conversations: Conversation[]
    isLoading: boolean
    userEmail: string

    setUserEmail: (email: string) => void
    sendMessage: (text: string) => Promise<void>
    loadConversations: () => Promise<void>
    openConversation: (id: string) => Promise<void>
    deleteConversation: (id: string) => Promise<void>
    startNewChat: () => void
}

export const useChatStore = create<ChatStore>((set, get) => ({
    messages: [],
    conversationId: null,
    conversations: [],
    isLoading: false,
    userEmail: 'anonymous',

    setUserEmail: (email) => set({ userEmail: email }),

    startNewChat: () =>
        set({
            messages: [],
            conversationId: null,
        }),

    loadConversations: async () => {
        try {
            const { data } = await chatApi.listConversations(get().userEmail)
            set({ conversations: data })
        } catch (e) {
            console.error('Failed to load conversations:', e)
        }
    },

    openConversation: async (id) => {
        if (get().isLoading) return
        try {
            const { data } = await chatApi.getConversation(id)
            const messages: Message[] = (data.messages || []).map(
                (m: { role: string; content: string; tool_calls?: unknown }) => ({
                    role: m.role as 'user' | 'assistant',
                    content: m.content,
                    tool_calls: m.tool_calls as Message['tool_calls'],
                }),
            )
            set({ conversationId: id, messages })
        } catch (e) {
            console.error('Failed to load conversation:', e)
        }
    },

    sendMessage: async (text) => {
        const { conversationId, userEmail } = get()

        // Optimistically add user message
        const userMsg: Message = { role: 'user', content: text }
        set((s) => ({ messages: [...s.messages, userMsg], isLoading: true }))

        try {
            const { data } = await chatApi.send(text, conversationId, userEmail)

            // Track new conversation
            if (data.conversation_id && !conversationId) {
                set({ conversationId: data.conversation_id })
                get().loadConversations()
            }

            // Build assistant message
            const assistantMsg: Message = {
                role: 'assistant',
                content: data.response,
                tool_calls: data.tool_calls
                    ? { calls: data.tool_calls as ToolCall[] }
                    : undefined,
            }

            set((s) => ({ messages: [...s.messages, assistantMsg] }))
        } catch (err) {
            const errorMsg: Message = {
                role: 'assistant',
                content: `⚠️ Error: ${err instanceof Error ? err.message : 'Unknown error'}. Make sure the backend is running.`,
            }
            set((s) => ({ messages: [...s.messages, errorMsg] }))
        } finally {
            set({ isLoading: false })
        }
    },

    deleteConversation: async (id) => {
        try {
            await chatApi.deleteConversation(id)
            set((s) => ({
                conversations: s.conversations.filter((c) => c.id !== id),
                ...(s.conversationId === id
                    ? { conversationId: null, messages: [] }
                    : {}),
            }))
        } catch (e) {
            console.error('Delete failed:', e)
        }
    },
}))
