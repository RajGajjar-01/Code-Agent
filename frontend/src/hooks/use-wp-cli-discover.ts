import { useState, useCallback } from 'react'
import { wpCliApi } from '@/lib/axios'

interface WpPathDiscovery {
    found: boolean
    path: string | null
    wp_config_exists: boolean | null
    cwd: string | null
    message: string | null
}

interface UseWpCliDiscoverResult {
    discovery: WpPathDiscovery | null
    isLoading: boolean
    error: string | null
    discover: () => Promise<void>
}

export function useWpCliDiscover(): UseWpCliDiscoverResult {
    const [discovery, setDiscovery] = useState<WpPathDiscovery | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const discover = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const { data } = await wpCliApi.discoverPath()
            setDiscovery(data)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to discover WordPress path')
            setDiscovery(null)
        } finally {
            setIsLoading(false)
        }
    }, [])

    return { discovery, isLoading, error, discover }
}
