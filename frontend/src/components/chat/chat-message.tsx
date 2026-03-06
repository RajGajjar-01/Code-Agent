import { Layers } from 'lucide-react'
import { ToolCallBadge } from '@/components/chat/tool-call-badge'
import type { Message } from '@/types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '@/lib/utils'

interface ChatMessageProps {
    message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.role === 'user'
    const hasAttachments = Boolean(message.attachments?.length)

    return (
        <div className={cn('px-4 py-3 animate-in fade-in slide-in-from-bottom-2 duration-300')}>
            <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
                {/* Avatar */}
                <div
                    className={cn(
                        'h-8 w-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-semibold mt-0.5',
                        isUser
                            ? 'bg-primary text-black'
                            : 'bg-secondary border text-foreground',
                    )}
                >
                    {isUser ? 'You' : <Layers className="h-4 w-4" />}
                </div>

                {/* Content */}
                <div className={cn('flex-1 min-w-0 flex flex-col', isUser && 'items-end')}>
                    <p className="text-[0.8rem] font-semibold text-muted-foreground mb-1">
                        {isUser ? 'You' : 'WP Agent'}
                    </p>

                    {isUser ? (
                        <>
                            {/* User bubble */}
                            {message.content || message.attachments?.length ? (
                                <div
                                    className={cn(
                                        'bg-secondary border rounded-lg rounded-tr-sm text-sm leading-relaxed max-w-[85%] text-left break-words overflow-hidden',
                                        hasAttachments ? 'px-2.5 py-2' : 'px-4 py-2.5',
                                    )}
                                >
                                    {message.attachments?.length ? (
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            {message.attachments.map((a) => (
                                                <a
                                                    key={a.id}
                                                    href={a.url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="block border rounded-lg overflow-hidden bg-muted"
                                                >
                                                    <img
                                                        src={a.url}
                                                        alt={a.filename}
                                                        className="h-24 w-24 object-cover"
                                                        loading="lazy"
                                                    />
                                                </a>
                                            ))}
                                        </div>
                                    ) : null}

                                    {message.content ? <div>{message.content}</div> : null}
                                </div>
                            ) : null}
                        </>
                    ) : (
                        /* Assistant markdown */
                        <div className="prose prose-sm max-w-full dark:prose-invert prose-pre:bg-muted prose-pre:border prose-code:text-sm text-[0.9rem] leading-[1.7] break-words overflow-hidden">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    code({ className, children, ...props }) {
                                        const match = /language-(\w+)/.exec(className || '')
                                        const codeString = String(children).replace(/\n$/, '')
                                        if (match) {
                                            return (
                                                <SyntaxHighlighter
                                                    style={oneLight}
                                                    language={match[1]}
                                                    PreTag="div"
                                                    className="rounded-lg !bg-muted text-sm overflow-x-auto"
                                                >
                                                    {codeString}
                                                </SyntaxHighlighter>
                                            )
                                        }
                                        return (
                                            <code className={className} {...props}>
                                                {children}
                                            </code>
                                        )
                                    },
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    )}

                    {message.tool_calls?.calls?.length ? (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                            {message.tool_calls.calls.map((tc, i) => (
                                <ToolCallBadge key={i} toolCall={tc} />
                            ))}
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    )
}
