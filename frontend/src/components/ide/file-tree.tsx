import { ChevronRight, Folder, File } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TreeNode } from '@/types'

const FILE_ICONS: Record<string, string> = {
    '.php': '🐘',
    '.js': '📜',
    '.jsx': '📜',
    '.ts': '📘',
    '.tsx': '📘',
    '.css': '🎨',
    '.json': '{}',
    '.html': '🌐',
    '.xml': '📋',
    '.svg': '🖼️',
    '.md': '📝',
}

interface FileTreeProps {
    nodes: TreeNode[]
    expandedPaths: Set<string>
    activePath: string | null
    onToggle: (path: string) => void
    onFileOpen: (path: string) => void
    depth: number
}

export function FileTree({ nodes, expandedPaths, activePath, onToggle, onFileOpen, depth }: FileTreeProps) {
    return (
        <div className="text-sm">
            {nodes.map((node) => {
                const isDir = node.type === 'directory'
                const isExpanded = expandedPaths.has(node.path)
                const isActive = activePath === node.path

                return (
                    <div key={node.path}>
                        <button
                            className={cn(
                                'flex w-full items-center gap-1 px-2 py-1 text-left hover:bg-muted/60 transition-colors',
                                isActive && 'bg-accent text-accent-foreground',
                            )}
                            style={{ paddingLeft: `${depth * 16 + 8}px` }}
                            onClick={() => {
                                if (isDir) onToggle(node.path)
                                else onFileOpen(node.path)
                            }}
                        >
                            {isDir ? (
                                <ChevronRight
                                    className={cn('h-3.5 w-3.5 shrink-0 transition-transform', isExpanded && 'rotate-90')}
                                />
                            ) : (
                                <span className="w-3.5 shrink-0" />
                            )}

                            {isDir ? (
                                <Folder className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                            ) : (
                                <span className="text-xs shrink-0">{FILE_ICONS[node.extension || ''] || '📄'}</span>
                            )}

                            <span className="truncate text-xs">{node.name}</span>
                        </button>

                        {isDir && isExpanded && node.children && (
                            <FileTree
                                nodes={node.children}
                                expandedPaths={expandedPaths}
                                activePath={activePath}
                                onToggle={onToggle}
                                onFileOpen={onFileOpen}
                                depth={depth + 1}
                            />
                        )}
                    </div>
                )
            })}
        </div>
    )
}
