import { useRef, useCallback } from 'react'
import { Send, Paperclip } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
    onSend: (text: string) => void
    disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    const handleSend = useCallback(() => {
        const text = textareaRef.current?.value.trim()
        if (!text || disabled) return
        onSend(text)
        if (textareaRef.current) {
            textareaRef.current.value = ''
            textareaRef.current.style.height = 'auto'
        }
    }, [onSend, disabled])

    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
            }
        },
        [handleSend],
    )

    const handleInput = useCallback(() => {
        const el = textareaRef.current
        if (el) {
            el.style.height = 'auto'
            el.style.height = Math.min(el.scrollHeight, 160) + 'px'
        }
    }, [])

    return (
        <div className="h-[110px] bg-background/90 backdrop-blur-md flex flex-col justify-center px-4 sm:px-6 shrink-0">
            <div className="max-w-4xl w-full mx-auto">
                {/* Input box */}
                <div className="flex items-end gap-2 px-4 py-2 rounded-xl border bg-background shadow-sm focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/10 transition-all">
                    <textarea
                        ref={textareaRef}
                        placeholder="Describe the WordPress site you want to build..."
                        className="flex-1 bg-transparent border-0 outline-none resize-none text-[0.9rem] leading-[1.5] min-h-6 max-h-[160px] py-1.5 text-foreground placeholder:text-muted-foreground"
                        rows={1}
                        onKeyDown={handleKeyDown}
                        onInput={handleInput}
                        autoFocus
                    />
                    <div className="flex items-center gap-1 shrink-0 pb-0.5">
                        <Button variant="ghost" size="icon" className="h-9 w-9 text-muted-foreground" type="button">
                            <Paperclip className="h-4 w-4" />
                        </Button>
                        <Button
                            size="icon"
                            className="h-9 w-9"
                            onClick={handleSend}
                            disabled={disabled}
                            type="button"
                        >
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
                <p className="text-center text-[0.72rem] text-muted-foreground mt-2 opacity-60">
                    WP Agent can make mistakes. Review generated content before publishing.
                </p>
            </div>
        </div>
    )
}
