import { useEffect, useRef, useCallback } from 'react'
import { AppHeader } from '@/components/layout/app-header'
import { ConnectorsPanel } from '@/components/drive/connectors-panel'
import { ChatMessage } from '@/components/chat/chat-message'
import { ChatInput } from '@/components/chat/chat-input'
import { WelcomeScreen } from '@/components/chat/welcome-screen'
import { TypingIndicator } from '@/components/chat/typing-indicator'
import { useChatStore } from '@/stores/chat-store'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useSidebarShortcuts } from '@/hooks/use-sidebar-shortcuts'
import { cn } from '@/lib/utils'

export function ChatPage() {
    const { messages, isLoading, conversationId, sendMessage } = useChatStore()
    const { connectorsPanelOpen } = useSidebarStore()
    const scrollRef = useRef<HTMLDivElement>(null)

    // Enable keyboard shortcuts
    useSidebarShortcuts()

    const scrollToBottom = useCallback(() => {
        requestAnimationFrame(() => {
            if (scrollRef.current) {
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight
            }
        })
    }, [])

    useEffect(() => {
        scrollToBottom()
    }, [messages, isLoading, scrollToBottom])

    const handleSend = useCallback((text: string) => sendMessage(text), [sendMessage])
    const handleSuggestionClick = useCallback((prompt: string) => sendMessage(prompt), [sendMessage])

    const showWelcome = !conversationId && messages.length === 0

    return (
        <div className="flex flex-1 overflow-hidden min-w-0">
            {/* Main chat area */}
            <div className="flex flex-1 flex-col min-w-0 bg-background h-screen">
                <AppHeader />

                {/* Messages / Welcome */}
                <div ref={scrollRef} className="flex-1 overflow-y-auto min-h-0">
                    {showWelcome ? (
                        <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
                    ) : (
                        <div className="max-w-3xl mx-auto">
                            {messages.map((msg, i) => (
                                <ChatMessage key={i} message={msg} />
                            ))}
                            {isLoading && <TypingIndicator />}
                        </div>
                    )}
                </div>

                <ChatInput onSend={handleSend} disabled={isLoading} />
            </div>

            {/* Right panel with transition */}
            <div
                className={cn(
                    'transition-all duration-200 ease-in-out overflow-hidden',
                    connectorsPanelOpen ? 'w-[300px]' : 'w-0'
                )}
            >
                {connectorsPanelOpen && <ConnectorsPanel />}
            </div>
        </div>
    )
}
