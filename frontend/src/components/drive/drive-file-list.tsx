import { Folder, File } from 'lucide-react'
import type { DriveItem } from '@/types'
import { cn } from '@/lib/utils'

const FOLDER_MIME = 'application/vnd.google-apps.folder'

interface DriveFileListProps {
    items: DriveItem[]
    onFolderClick: (id: string, name: string) => void
}

export function DriveFileList({ items, onFolderClick }: DriveFileListProps) {
    if (!items.length) {
        return (
            <div className="py-10 text-center text-[0.8rem] text-muted-foreground italic">
                No files found in this folder.
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-1">
            {items.map((item) => {
                const isFolder = item.mime_type === FOLDER_MIME
                const dateMeta = item.modified_time
                    ? new Date(item.modified_time).toLocaleDateString()
                    : ''

                return (
                    <button
                        key={item.id}
                        onClick={() => isFolder && onFolderClick(item.id, item.name)}
                        className="flex items-center gap-3 w-full rounded-lg px-2.5 py-2.5 text-left border border-transparent hover:bg-background hover:border-border hover:shadow-sm transition-all group min-w-0"
                    >
                        {/* Icon Container using Theme Colors */}
                        <div
                            className={cn(
                                'h-9 w-9 rounded-md flex items-center justify-center shrink-0 transition-colors',
                                isFolder
                                    ? 'bg-folder text-folder-foreground'
                                    : 'bg-secondary text-muted-foreground',
                            )}
                        >
                            {isFolder ? (
                                <Folder className="w-4 h-4 fill-current" />
                            ) : (
                                <File className="w-4 h-4" />
                            )}
                        </div>

                        {/* File Info */}
                        <div className="flex-1 min-w-0">
                            <h5 className="text-[0.85rem] font-bold text-foreground truncate leading-tight">
                                {item.name}
                            </h5>
                            {dateMeta && (
                                <p className="text-[0.7rem] text-muted-foreground mt-0.5 opacity-60">
                                    {dateMeta}
                                </p>
                            )}
                        </div>
                    </button>
                )
            })}
        </div>
    )
}
