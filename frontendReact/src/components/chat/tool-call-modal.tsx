import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import type { ToolCall } from '@/types'

interface ToolCallModalProps {
    toolCall: ToolCall
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function ToolCallModal({ toolCall, open, onOpenChange }: ToolCallModalProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>Tool Execution</DialogTitle>
                </DialogHeader>

                <div className="space-y-4 text-sm">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-muted-foreground">Function:</span>
                        <span className="font-mono">{toolCall.name}</span>
                    </div>

                    <div className="flex items-center gap-2">
                        <span className="font-medium text-muted-foreground">Status:</span>
                        <Badge variant={toolCall.status === 'success' ? 'default' : 'secondary'}>
                            {toolCall.status || 'pending'}
                        </Badge>
                    </div>

                    <div>
                        <span className="font-medium text-muted-foreground">Arguments:</span>
                        <pre className="mt-1 rounded-lg bg-muted p-3 text-xs overflow-x-auto">
                            {JSON.stringify(toolCall.arguments || {}, null, 2)}
                        </pre>
                    </div>

                    {toolCall.result !== undefined && (
                        <div>
                            <span className="font-medium text-muted-foreground">Result:</span>
                            <pre className="mt-1 rounded-lg bg-muted p-3 text-xs overflow-x-auto">
                                {JSON.stringify(toolCall.result, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
