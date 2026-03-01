import { create } from 'zustand'
import { toast } from 'sonner'
import { chatApi } from '@/lib/axios'
import type { Conversation, Message, ToolCall } from '@/types'
import { useUserStore } from './user-store'
import { useSettingsStore } from './settings-store'

interface ChatStore {
    messages: Message[]
    conversationId: string | null
    conversations: Conversation[]
    isLoading: boolean

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

    startNewChat: () =>
        set({
            messages: [],
            conversationId: null,
        }),

    loadConversations: async () => {
        try {
            const { email, isAuthenticated } = useUserStore.getState()
            
            if (!isAuthenticated || !email) {
                console.warn('User not authenticated, skipping conversation load')
                return
            }
            
            const { data } = await chatApi.listConversations(email)
            set({ conversations: data })
        } catch (e) {
            console.error('Failed to load conversations:', e)
            if (e instanceof Error && e.message.includes('Authentication required')) {
                toast.error('Please log in to view conversations')
            }
        }
    },

    openConversation: async (id) => {
        if (get().isLoading) return
        
        const { isAuthenticated } = useUserStore.getState()
        if (!isAuthenticated) {
            toast.error('Please log in to view conversations')
            return
        }
        
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
            toast.error('Failed to load conversation')
        }
    },

    sendMessage: async (text) => {
        const { email, isAuthenticated } = useUserStore.getState()
        
        // Check authentication before sending
        if (!isAuthenticated || !email) {
            toast.error('Please log in to send messages')
            // Redirect to login
            window.location.href = '/login'
            return
        }
        
        const { conversationId } = get()
        const llmProvider = useSettingsStore.getState().llmProvider

        // Optimistically add user message
        const userMsg: Message = { role: 'user', content: text }
        set((s) => ({ messages: [...s.messages, userMsg], isLoading: true }))

        try {
            const { data } = await chatApi.send(text, conversationId, email, llmProvider)

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
            let errorMessage = 'Unknown error'
            
            if (err instanceof Error) {
                errorMessage = err.message
                
                // Handle authentication errors
                if (err.message.includes('Authentication required')) {
                    toast.error('Please log in to send messages')
                    window.location.href = '/login'
                    return
                }
            }
            
            const errorMsg: Message = {
                role: 'assistant',
                content: `⚠️ Error: ${errorMessage}. Make sure the backend is running.`,
            }
            set((s) => ({ messages: [...s.messages, errorMsg] }))
            toast.error('Failed to send message')
        } finally {
            set({ isLoading: false })
        }
    },

    deleteConversation: async (id) => {
        const { isAuthenticated } = useUserStore.getState()
        
        if (!isAuthenticated) {
            toast.error('Please log in to delete conversations')
            return
        }
        
        try {
            await chatApi.deleteConversation(id)
            set((s) => ({
                conversations: s.conversations.filter((c) => c.id !== id),
                ...(s.conversationId === id
                    ? { conversationId: null, messages: [] }
                    : {}),
            }))
            toast.success('Conversation deleted')
        } catch (e) {
            console.error('Delete failed:', e)
            toast.error('Failed to delete conversation')
        }
    },
}))
