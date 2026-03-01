import { Link } from 'react-router'
import { MessageSquare, Save, WrapText } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { SidebarTrigger } from '@/components/ui/sidebar'

interface IdeHeaderProps {
    fileInfo: string
    wordWrap: boolean
    onToggleWrap: () => void
    onSave: () => void
}

export function IdeHeader({ fileInfo, wordWrap, onToggleWrap, onSave }: IdeHeaderProps) {
    return (
        <header className="flex items-center justify-between h-[60px] px-5 border-b bg-background/85 backdrop-blur-md shrink-0 z-[100]">
            <div className="flex items-center gap-3 min-w-0">
                <SidebarTrigger />
                <h1 className="text-[0.95rem] font-semibold tracking-[-0.01em] truncate max-w-[300px]">
                    {fileInfo || 'WP Agent IDE'}
                </h1>
            </div>

            <div className="flex items-center gap-3">
                {/* Word wrap toggle */}
                <Badge variant="outline" className="rounded-full gap-1.5 text-xs font-medium hidden sm:flex">
                    <WrapText className="h-3 w-3" />
                    Wrap: {wordWrap ? 'On' : 'Off'}
                </Badge>

                {/* Save button */}
                <Button variant="outline" size="sm" className="rounded-full gap-1.5" onClick={onSave}>
                    <Save className="h-3.5 w-3.5" />
                    Save
                </Button>

                {/* Chat link */}
                <Button variant="outline" size="sm" className="rounded-full gap-1.5 text-primary border-primary" asChild>
                    <Link to="/">
                        <MessageSquare className="h-3.5 w-3.5" />
                        Chat
                    </Link>
                </Button>
            </div>
        </header>
    )
}
