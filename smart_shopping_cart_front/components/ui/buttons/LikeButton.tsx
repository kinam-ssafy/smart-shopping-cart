'use client';

import { useState } from 'react';
import HeartIcon from '../../icons/HeartIcon';

interface LikeButtonProps {
    /** 초기 좋아요 개수 */
    initialCount?: number;

    /** 초기 좋아요 상태 */
    initialLiked?: boolean;

    /** 좋아요 상태 변경 핸들러 */
    onLikeChange?: (liked: boolean, count: number) => void;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 좋아요 버튼 컴포넌트
 * 하트 아이콘 + 좋아요 개수 표시
 */
export default function LikeButton({
    initialCount = 0,
    initialLiked = false,
    onLikeChange,
    className = '',
}: LikeButtonProps) {
    const [liked, setLiked] = useState(initialLiked);
    const [count, setCount] = useState(initialCount);

    const handleClick = () => {
        const newLiked = !liked;
        const newCount = newLiked ? count + 1 : count - 1;

        setLiked(newLiked);
        setCount(newCount);

        if (onLikeChange) {
            onLikeChange(newLiked, newCount);
        }
    };

    return (
        <button
            onClick={handleClick}
            className={`
        flex flex-col items-center gap-1
        transition-all duration-200
        ${className}
      `}
        >
            {/* 하트 아이콘 */}
            <div className={`
        transition-all duration-200
        ${liked ? 'text-red-500 scale-110' : 'text-gray-400'}
      `}>
                <HeartIcon size={24} filled={liked} />
            </div>

            {/* 좋아요 개수 */}
            <span className={`
        text-xs font-medium
        transition-colors duration-200
        ${liked ? 'text-red-500' : 'text-gray-500'}
      `}>
                {count}
            </span>
        </button>
    );
}
