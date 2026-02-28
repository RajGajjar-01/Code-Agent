import { useState } from 'react'
import { Wrench } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { ToolCallModal } from '@/components/chat/tool-call-modal'
import type { ToolCall } from '@/types'

interface ToolCallBadgeProps {
    toolCall: ToolCall
}

export function ToolCallBadge({ toolCall }: ToolCallBadgeProps) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <>
            <Badge
                variant={toolCall.status === 'success' ? 'default' : 'secondary'}
                className="gap-1 cursor-pointer hover:bg-primary/80 transition-colors text-xs"
                onClick={() => setIsOpen(true)}
            >
                <Wrench className="h-3 w-3" />
                Tool: {toolCall.name || toolCall.function || 'tool'}
            </Badge>
            <ToolCallModal toolCall={toolCall} open={isOpen} onOpenChange={setIsOpen} />
        </>
    )
}
