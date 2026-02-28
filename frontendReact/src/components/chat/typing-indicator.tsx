export function TypingIndicator() {
    return (
        <div className="flex gap-3 py-4 px-4 bg-muted/30">
            <div className="h-8 w-8 shrink-0 rounded-full bg-secondary flex items-center justify-center mt-0.5">
                <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-secondary-foreground"
                >
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                </svg>
            </div>
            <div className="flex-1 space-y-1">
                <p className="text-xs font-semibold text-muted-foreground">WP Agent</p>
                <div className="flex items-center gap-1 py-2">
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:0ms]" />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:150ms]" />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:300ms]" />
                </div>
            </div>
        </div>
    )
}
