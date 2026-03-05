import { useRef, useCallback, useMemo, useState } from 'react'
import { Send, Paperclip, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
    onSend: (text: string, files?: File[]) => void
    disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [pendingFiles, setPendingFiles] = useState<File[]>([])

    const previewUrls = useMemo(
        () => pendingFiles.map((f) => ({ file: f, url: URL.createObjectURL(f) })),
        [pendingFiles],
    )

    const addFiles = useCallback((files: File[]) => {
        if (!files.length) return
        const imagesOnly = files.filter((f) => f.type.startsWith('image/'))
        if (!imagesOnly.length) return
        setPendingFiles((prev) => {
            const next = [...prev, ...imagesOnly]
            return next.slice(0, 5)
        })
    }, [])

    const removeFile = useCallback((idx: number) => {
        setPendingFiles((prev) => prev.filter((_, i) => i !== idx))
    }, [])

    const handlePickFiles = useCallback(() => {
        if (disabled) return
        fileInputRef.current?.click()
    }, [disabled])

    const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || [])
        addFiles(files)
        e.target.value = ''
    }, [addFiles])

    const handleSend = useCallback(() => {
        const text = textareaRef.current?.value.trim()
        if (disabled) return
        if (!text && pendingFiles.length === 0) return
        onSend(text || '', pendingFiles.length ? pendingFiles : undefined)
        if (textareaRef.current) {
            textareaRef.current.value = ''
            textareaRef.current.style.height = 'auto'
        }
        setPendingFiles([])
    }, [onSend, disabled, pendingFiles])

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

    const handlePaste = useCallback((e: React.ClipboardEvent<HTMLTextAreaElement>) => {
        const items = e.clipboardData?.items
        if (!items?.length) return

        const pastedFiles: File[] = []
        for (const item of items) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                const file = item.getAsFile()
                if (file) pastedFiles.push(file)
            }
        }

        if (pastedFiles.length) {
            e.preventDefault()
            addFiles(pastedFiles)
        }
    }, [addFiles])

    return (
        <div className="min-h-[110px] py-4 bg-background/90 backdrop-blur-md flex flex-col justify-center px-4 sm:px-6 shrink-0">
            <div className="max-w-4xl w-full mx-auto">
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={handleFileChange}
                />

                {/* Input box */}
                <div className="px-4 py-2 rounded-lg border bg-background shadow-sm focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/10 transition-all">
                    {pendingFiles.length ? (
                        <div className="mb-2 flex gap-2 overflow-x-auto">
                            {previewUrls.map((p, idx) => (
                                <div key={idx} className="relative h-16 w-16 rounded-md overflow-hidden border bg-muted shrink-0">
                                    <img
                                        src={p.url}
                                        alt={p.file.name}
                                        className="h-full w-full object-cover"
                                    />
                                    <button
                                        type="button"
                                        aria-label="Remove attachment"
                                        className="absolute top-1 right-1 h-6 w-6 rounded-full bg-background/90 border shadow-sm flex items-center justify-center hover:bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        onClick={() => removeFile(idx)}
                                    >
                                        <X className="h-3.5 w-3.5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : null}

                    <div className="flex items-end gap-2">
                        <textarea
                            ref={textareaRef}
                            placeholder="Describe the WordPress site you want to build..."
                            className="flex-1 bg-transparent border-0 outline-none resize-none text-[0.9rem] leading-[1.5] min-h-6 max-h-[160px] py-1.5 text-foreground placeholder:text-muted-foreground"
                            rows={1}
                            onKeyDown={handleKeyDown}
                            onInput={handleInput}
                            onPaste={handlePaste}
                            autoFocus
                        />
                        <div className="flex items-center gap-1 shrink-0 pb-0.5">
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-9 w-9 text-muted-foreground"
                                type="button"
                                onClick={handlePickFiles}
                                disabled={disabled}
                            >
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
                </div>
                <p className="text-center text-[0.72rem] text-muted-foreground mt-2 opacity-60">
                    WP Agent can make mistakes. Review generated content before publishing.
                </p>
            </div>
        </div>
    )
}
