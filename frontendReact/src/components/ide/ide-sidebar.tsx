import { Layers } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { FileTree } from '@/components/ide/file-tree'
import { useIdeStore } from '@/stores/ide-store'
import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
} from '@/components/ui/sidebar'

interface IdeSidebarProps {
    onCreateRequest: (parentPath: string, type: 'file' | 'directory') => void
}

export function IdeSidebar({ onCreateRequest }: IdeSidebarProps) {
    const {
        roots,
        currentRoot,
        treeData,
        expandedPaths,
        activePath,
        isTreeLoading,
        setCurrentRoot,
        toggleExpanded,
        openFile,
    } = useIdeStore()

    return (
        <Sidebar collapsible="offcanvas" side="left">
            <SidebarHeader className="border-b border-sidebar-border h-[60px] p-0">
                <div className="flex items-center gap-2.5 px-5 h-full">
                    <div className="flex items-center justify-center h-8 w-8 shrink-0">
                        <Layers className="h-6 w-6 text-sidebar-foreground" strokeWidth={2.5} />
                    </div>
                    <span className="text-lg font-bold text-sidebar-foreground tracking-tight whitespace-nowrap flex-1">
                        WP Agent
                    </span>
                </div>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup className="px-0">
                    <SidebarGroupLabel className="px-2">Workspace</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <div className="flex flex-wrap gap-1 px-2 pb-2">
                            {roots.map((root) => (
                                <Button
                                    key={root.path}
                                    size="sm"
                                    variant={currentRoot === root.path ? 'default' : 'outline'}
                                    className="text-xs h-7"
                                    onClick={() => setCurrentRoot(root.path)}
                                >
                                    {root.name === 'Themes' ? '🎨' : root.name === 'Plugins' ? '🔌' : '⚡'} {root.name}
                                </Button>
                            ))}
                        </div>
                    </SidebarGroupContent>
                </SidebarGroup>

                <SidebarGroup className="px-0">
                    <SidebarGroupContent>
                        {isTreeLoading ? (
                            <div className="px-2 space-y-2">
                                {Array.from({ length: 8 }).map((_, i) => (
                                    <Skeleton key={i} className="h-6 w-full" />
                                ))}
                            </div>
                        ) : (
                            <FileTree
                                nodes={treeData}
                                expandedPaths={expandedPaths}
                                activePath={activePath}
                                onToggle={toggleExpanded}
                                onFileOpen={openFile}
                                depth={0}
                            />
                        )}
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
    )
}
