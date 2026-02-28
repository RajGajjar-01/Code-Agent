import { Code2 } from 'lucide-react'

export function IdeWelcome() {
    return (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center text-muted-foreground">
            <Code2 className="h-16 w-16 opacity-20" />
            <h2 className="text-xl font-semibold text-foreground/60">WordPress Code Editor</h2>
            <p className="text-sm max-w-xs">
                Select a file from the sidebar to start editing.
                <br />
                Only themes and plugins are editable.
            </p>
            <p className="text-xs">
                Press <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px] font-mono">Ctrl+S</kbd> to save.
            </p>
        </div>
    )
}
