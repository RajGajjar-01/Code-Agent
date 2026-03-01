import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router'
import { ThemeProvider } from 'next-themes'
import { Toaster } from 'sonner'
import { Loader2 } from 'lucide-react'
import { RootLayout } from '@/components/layout/root-layout'
import { ChatPage } from '@/pages/chat-page'
import { IdePage } from '@/pages/ide-page'
import { LoginPage } from '@/pages/login-page'
import { SignupPage } from '@/pages/signup-page'
import { useUserStore } from '@/stores/user-store'

function AuthGuard() {
    const { isAuthenticated, isLoading } = useUserStore()

    if (isLoading) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return <Outlet />
}

function GuestGuard() {
    const { isAuthenticated, isLoading } = useUserStore()

    if (isLoading) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    if (isAuthenticated) {
        return <Navigate to="/" replace />
    }

    return <Outlet />
}

export default function App() {
    const checkSession = useUserStore((s) => s.checkSession)

    useEffect(() => {
        checkSession()
    }, [])

    return (
        <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light">
            <BrowserRouter>
                <Routes>
                    {/* Public routes — only for guests */}
                    <Route element={<GuestGuard />}>
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/signup" element={<SignupPage />} />
                    </Route>

                    {/* Protected routes — require auth */}
                    <Route element={<AuthGuard />}>
                        <Route element={<RootLayout />}>
                            <Route index element={<ChatPage />} />
                        </Route>
                        <Route path="/ide" element={<IdePage />} />
                    </Route>
                </Routes>
            </BrowserRouter>
            <Toaster richColors position="bottom-right" />
        </ThemeProvider>
    )
}