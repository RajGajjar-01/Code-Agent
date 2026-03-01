import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Layers, Eye, EyeOff, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useUserStore } from '@/stores/user-store'
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth'

export function SignupPage() {
    const navigate = useNavigate()
    const register = useUserStore((s) => s.register)

    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [error, setError] = useState('')

    const {
        register: registerField,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
    })

    const onSubmit = async (data: RegisterFormData) => {
        setError('')

        try {
            await register(data.email, data.name, data.password)
            navigate('/')
        } catch (err: any) {
            if (err?.response?.status === 409) {
                setError('Email already registered')
            } else if (err?.response?.data?.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    setError(err.response.data.detail[0]?.msg || 'Registration failed')
                } else {
                    setError(err.response.data.detail)
                }
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
                        <Layers className="h-7 w-7 text-primary-foreground" />
                    </div>
                    <div className="text-center">
                        <h1 className="text-2xl font-bold tracking-tight">Create an account</h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Get started with WP Agent
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
                        <label htmlFor="signup-name" className="text-sm font-medium">
                            Full Name
                        </label>
                        <Input
                            id="signup-name"
                            type="text"
                            placeholder="John Doe"
                            {...registerField('name')}
                            autoComplete="name"
                            className="h-11"
                        />
                        {errors.name && (
                            <p className="text-sm text-destructive">{errors.name.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="signup-email" className="text-sm font-medium">
                            Email
                        </label>
                        <Input
                            id="signup-email"
                            type="email"
                            placeholder="you@example.com"
                            {...registerField('email')}
                            autoComplete="email"
                            className="h-11"
                        />
                        {errors.email && (
                            <p className="text-sm text-destructive">{errors.email.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="signup-password" className="text-sm font-medium">
                            Password
                        </label>
                        <div className="relative">
                            <Input
                                id="signup-password"
                                type={showPassword ? 'text' : 'password'}
                                placeholder="At least 8 characters"
                                {...registerField('password')}
                                autoComplete="new-password"
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

                    <div className="space-y-2">
                        <label htmlFor="signup-confirm" className="text-sm font-medium">
                            Confirm Password
                        </label>
                        <div className="relative">
                            <Input
                                id="signup-confirm"
                                type={showConfirmPassword ? 'text' : 'password'}
                                placeholder="Repeat your password"
                                {...registerField('confirmPassword')}
                                autoComplete="new-password"
                                className="h-11 pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                tabIndex={-1}
                            >
                                {showConfirmPassword ? (
                                    <EyeOff className="h-4 w-4" />
                                ) : (
                                    <Eye className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                        {errors.confirmPassword && (
                            <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
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
                                Creating account...
                            </>
                        ) : (
                            'Create Account'
                        )}
                    </Button>
                </form>

                {/* Footer */}
                <p className="text-center text-sm text-muted-foreground">
                    Already have an account?{' '}
                    <Link
                        to="/login"
                        className="text-primary font-semibold hover:underline underline-offset-4"
                    >
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    )
}
