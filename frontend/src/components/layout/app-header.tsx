import { SidebarTrigger } from '@/components/ui/sidebar'
import { ModelSelector } from '@/components/chat/model-selector'
import { useChatStore } from '@/stores/chat-store'

export function AppHeader() {
    const { conversationId, messages } = useChatStore()

    const title = conversationId
        ? messages.find((m) => m.role === 'user')?.content.slice(0, 50) || 'WordPress Agent'
        : 'WordPress Agent'

    return (
        <header className="flex items-center justify-between h-[60px] px-5 border-b bg-background/85 backdrop-blur-md shrink-0 z-10">
            <div className="flex items-center gap-3 min-w-0">
                <SidebarTrigger />
                <h1 className="text-[0.95rem] font-semibold tracking-[-0.01em] truncate max-w-[300px]">
                    {title}
                </h1>
            </div>

            <div className="flex items-center gap-3">
                <ModelSelector />
            </div>
        </header>
    )
}
