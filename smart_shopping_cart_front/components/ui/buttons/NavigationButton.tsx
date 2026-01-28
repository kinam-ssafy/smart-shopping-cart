'use client';

import React from 'react';
import LocationIcon from '../../icons/LocationIcon';

interface NavigationButtonProps {
    /** 클릭 핸들러 */
    onClick?: () => void;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 길찾기 버튼 컴포넌트
 * 상품 위치로 길찾기 기능을 제공
 */
export default function NavigationButton({
    onClick,
    className = '',
}: NavigationButtonProps) {
    return (
        <button
            onClick={onClick}
            className={`
        flex items-center gap-2
        px-4 py-2
        rounded-lg
        bg-white
        border border-gray-200
        text-gray-700
        hover:bg-gray-50
        transition-all duration-200
        cursor-pointer
        ${className}
      `}
            aria-label="Navigate"
        >
            <LocationIcon size={16} />
            <span className="text-sm font-medium">Navigate</span>
        </button>
    );
}
