import { Outlet } from 'react-router'
import { TooltipProvider } from '@/components/ui/tooltip'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { useSidebarStore } from '@/stores/sidebar-store'

export function RootLayout() {
    const { appSidebarOpen, setAppSidebarOpen } = useSidebarStore()

    return (
        <TooltipProvider>
            <SidebarProvider open={appSidebarOpen} onOpenChange={setAppSidebarOpen}>
                <AppSidebar />
                <Outlet />
            </SidebarProvider>
        </TooltipProvider>
    )
}
