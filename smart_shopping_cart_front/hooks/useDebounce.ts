import { useState, useEffect } from 'react';

/**
 * useDebounce Hook
 * 
 * 입력된 값(value)이 변경되면 delay(ms)만큼 기다린 후 debouncedValue를 업데이트합니다.
 * delay 이내에 값이 다시 변경되면 타이머가 초기화됩니다.
 * 
 * @param value 디바운싱할 값
 * @param delay 지연 시간 (ms)
 * @returns 디바운싱된 값
 */
export default function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}
