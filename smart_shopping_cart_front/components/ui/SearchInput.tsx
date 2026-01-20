'use client';

import React, { useState } from 'react';
import SearchIcon from '../icons/SearchIcon';

interface SearchInputProps {
    /** 플레이스홀더 텍스트 */
    placeholder?: string;

    /** 검색 버튼 클릭 핸들러 */
    onSearch?: (value: string) => void;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 검색 버튼이 포함된 SearchInput 컴포넌트
 */
export default function SearchInput({
    placeholder = '검색...',
    onSearch,
    className = '',
}: SearchInputProps) {
    const [value, setValue] = useState('');

    const handleSearch = () => {
        if (onSearch) {
            onSearch(value);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        setValue(newValue);
        // 실시간 검색: 타이핑할 때마다 onSearch 호출
        if (onSearch) {
            onSearch(newValue);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className={`relative ${className}`}>
            <input
                type="search"
                placeholder={placeholder}
                value={value}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                className="
          w-full
          h-[49px]
          pl-4
          pr-12
          bg-[#EEF1F4]
          rounded-[15px]
          border-none
          outline-none
          text-gray-800
          placeholder:text-gray-500
          transition-all duration-200
          focus:bg-[#E5E9ED]
        "
            />
            <button
                onClick={handleSearch}
                className="
          absolute
          right-2
          top-1/2
          -translate-y-1/2
          w-10
          h-10
          flex
          items-center
          justify-center
          rounded-lg
          hover:bg-white/50
          transition-all
          duration-200
        "
                aria-label="검색"
            >
                <SearchIcon size={20} />
            </button>
        </div>
    );
}
