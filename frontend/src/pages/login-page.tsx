import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Layers, Eye, EyeOff, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useUserStore } from '@/stores/user-store'
import { loginSchema, type LoginFormData } from '@/lib/validations/auth'

export function LoginPage() {
    const navigate = useNavigate()
    const login = useUserStore((s) => s.login)

    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
    })

    const onSubmit = async (data: LoginFormData) => {
        setError('')

        try {
            await login(data.email, data.password)
            navigate('/')
        } catch (err: any) {
            if (err?.response?.status === 401) {
                setError('Invalid email or password')
            } else if (err?.response?.status === 429) {
                setError('Too many attempts. Please try again later.')
            } else if (err?.response?.data?.detail) {
                setError(err.response.data.detail)
            } else {
                setError('An error occurred. Please try again.')
            }
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
            <div className="w-full max-w-[400px] space-y-8">
                {/* Logo */}
                <div className="flex flex-col items-center gap-3">
                    <div className="h-14 w-14 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
                        <Layers className="h-7 w-7 text-black" />
                    </div>
                    <div className="text-center">
                        <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Sign in to your WP Agent account
                        </p>
                    </div>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {error && (
                        <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-lg px-4 py-3 animate-in fade-in slide-in-from-top-1">
                            {error}
                        </div>
                    )}

                    <div className="space-y-2">
                        <label htmlFor="login-email" className="text-sm font-medium">
                            Email
                        </label>
                        <Input
                            id="login-email"
                            type="email"
                            placeholder="you@example.com"
                            {...register('email')}
                            autoComplete="email"
                            className="h-11"
                        />
                        {errors.email && (
                            <p className="text-sm text-destructive">{errors.email.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="login-password" className="text-sm font-medium">
                            Password
                        </label>
                        <div className="relative">
                            <Input
                                id="login-password"
                                type={showPassword ? 'text' : 'password'}
                                placeholder="Enter your password"
                                {...register('password')}
                                autoComplete="current-password"
                                className="h-11 pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                tabIndex={-1}
                            >
                                {showPassword ? (
                                    <EyeOff className="h-4 w-4" />
                                ) : (
                                    <Eye className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                        {errors.password && (
                            <p className="text-sm text-destructive">{errors.password.message}</p>
                        )}
                    </div>

                    <Button
                        type="submit"
                        className="w-full h-11 font-semibold text-[0.9rem]"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Signing in...
                            </>
                        ) : (
                            'Sign In'
                        )}
                    </Button>
                </form>

                {/* Footer */}
                <p className="text-center text-sm text-muted-foreground">
                    Don't have an account?{' '}
                    <Link
                        to="/signup"
                        className="text-primary font-semibold hover:underline underline-offset-4"
                    >
                        Sign up
                    </Link>
                </p>
            </div>
        </div>
    )
}
