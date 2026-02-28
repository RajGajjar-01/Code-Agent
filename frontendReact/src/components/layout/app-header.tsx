import { Link } from 'react-router'
import { FileCode2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { SidebarTrigger } from '@/components/ui/sidebar'
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
                {/* Model badge */}
                <Badge variant="outline" className="rounded-full gap-1.5 text-xs font-medium hidden sm:flex">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-600" />
                    Groq — LLaMA 3.3 70B
                </Badge>

                {/* IDE link */}
                <Button variant="outline" size="sm" className="rounded-full gap-1.5 text-primary border-primary" asChild>
                    <Link to="/ide">
                        <FileCode2 className="h-3.5 w-3.5" />
                        IDE
                    </Link>
                </Button>
            </div>
        </header>
    )
}
