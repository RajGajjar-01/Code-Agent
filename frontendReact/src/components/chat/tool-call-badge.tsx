import { Wrench } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { ToolCall } from '@/types'

interface ToolCallBadgeProps {
    toolCall: ToolCall
}

export function ToolCallBadge({ toolCall }: ToolCallBadgeProps) {
    return (
        <Badge
            variant="outline"
            className="gap-1 transition-colors text-xs bg-primary/10"
        >
            <Wrench className="h-3 w-3" />
            Tool: {toolCall.name || toolCall.function || 'tool'}
        </Badge>
    )
}
