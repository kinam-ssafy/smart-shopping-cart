'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface NavigationPathContextType {
    /** 경로 좌표 배열 [[x, y], [x, y], ...] */
    path: number[][] | null;
    /** 경로 설정 */
    setPath: (path: number[][] | null) => void;
    /** 경로 초기화 */
    clearPath: () => void;
    /** 로딩 상태 */
    isLoading: boolean;
    /** 로딩 상태 설정 */
    setIsLoading: (loading: boolean) => void;
}

const NavigationPathContext = createContext<NavigationPathContextType | undefined>(undefined);

export function NavigationPathProvider({ children }: { children: ReactNode }) {
    const [path, setPath] = useState<number[][] | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const clearPath = () => setPath(null);

    return (
        <NavigationPathContext.Provider value={{ path, setPath, clearPath, isLoading, setIsLoading }}>
            {children}
        </NavigationPathContext.Provider>
    );
}

export function useNavigationPath() {
    const context = useContext(NavigationPathContext);
    if (context === undefined) {
        throw new Error('useNavigationPath must be used within a NavigationPathProvider');
    }
    return context;
}

/**
 * Navigation API 호출 유틸리티
 */
export async function fetchNavigationPath(productId: number | string): Promise<number[][]> {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${API_URL}/api/map/navigation?productId=${productId}`);

    if (!response.ok) {
        throw new Error('Failed to fetch navigation path');
    }

    const data = await response.json();
    return data.path || [];
}
