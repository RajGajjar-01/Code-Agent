import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TabData } from '@/types'

interface EditorTabsProps {
    tabs: Map<string, TabData>
    activePath: string | null
    onActivate: (path: string) => void
    onClose: (path: string) => void
}

export function EditorTabs({ tabs, activePath, onActivate, onClose }: EditorTabsProps) {
    if (tabs.size === 0) return null

    return (
        <div className="flex bg-sidebar border-b overflow-x-auto scrollbar-none shrink-0 min-h-[38px]">
            {Array.from(tabs.entries()).map(([path, tab]) => {
                const name = path.split('/').pop() || path
                const isActive = path === activePath

                return (
                    <button
                        key={path}
                        className={cn(
                            'relative flex items-center gap-1.5 px-3.5 min-w-[110px] max-w-[200px] text-xs border-r shrink-0 cursor-pointer transition-colors whitespace-nowrap',
                            isActive
                                ? 'bg-background text-foreground font-medium after:absolute after:top-0 after:left-0 after:right-0 after:h-[2px] after:bg-primary'
                                : 'text-muted-foreground hover:bg-accent',
                        )}
                        onClick={() => onActivate(path)}
                        title={path}
                    >
                        {tab.isDirty && (
                            <span className="h-2 w-2 rounded-full bg-primary shrink-0" />
                        )}
                        <span className="truncate flex-1">{name}</span>
                        <span
                            className="ml-1 rounded p-0.5 hover:bg-muted shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={(e) => {
                                e.stopPropagation()
                                onClose(path)
                            }}
                        >
                            <X className="h-3 w-3" />
                        </span>
                    </button>
                )
            })}
        </div>
    )
}
