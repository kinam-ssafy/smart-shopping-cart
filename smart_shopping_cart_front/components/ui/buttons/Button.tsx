'use client';

import React from 'react';
import SearchIcon from '../../icons/SearchIcon';
import BackIcon from '../../icons/BackIcon';
import MenuIcon from '../../icons/MenuIcon';

interface IconButtonProps {
    /** 버튼 타입 */
    type: 'search' | 'back' | 'menu';

    /** 클릭 핸들러 */
    onClick?: () => void;

    /** 버튼 크기 */
    size?: 'small' | 'medium' | 'large';

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 아이콘 버튼 컴포넌트
 * 검색, 뒤로가기, 햄버거 메뉴 버튼만 제공
 */
export default function IconButton({
    type,
    onClick,
    size = 'medium',
    className = '',
}: IconButtonProps) {

    // 크기별 스타일
    const sizeStyles = {
        small: 'w-8 h-8',
        medium: 'w-10 h-10',
        large: 'w-12 h-12',
    };

    // 아이콘 크기 (픽셀)
    const iconSizes = {
        small: 16,
        medium: 20,
        large: 24,
    };

    // 아이콘 렌더링
    const renderIcon = () => {
        const iconSize = iconSizes[size];

        switch (type) {
            case 'search':
                return <SearchIcon size={iconSize} />;

            case 'back':
                return <BackIcon size={iconSize} />;

            case 'menu':
                return <MenuIcon size={iconSize} />;
        }
    };

    return (
        <button
            onClick={onClick}
            className={`
        ${sizeStyles[size]}
        flex items-center justify-center
        rounded-lg
        bg-transparent
        text-gray-700
        hover:bg-gray-100
        transition-all duration-200
        cursor-pointer
        ${className}
      `}
            aria-label={type}
        >
            {renderIcon()}
        </button>
    );
}

// 개별 버튼 컴포넌트 (사용 편의성)
export function SearchButton(props: Omit<IconButtonProps, 'type'>) {
    return <IconButton type="search" {...props} />;
}

export function BackButton(props: Omit<IconButtonProps, 'type'>) {
    return <IconButton type="back" {...props} />;
}

export function MenuButton(props: Omit<IconButtonProps, 'type'>) {
    return <IconButton type="menu" {...props} />;
}
