'use client';

import { MenuButton } from '@/components/ui/buttons/Button';

interface SectionHeaderProps {
    /** 섹션 제목 */
    title: string;

    /** 메뉴 버튼 클릭 핸들러 */
    onMenuClick?: () => void;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 섹션 헤더 컴포넌트
 * 제목과 햄버거 메뉴 버튼을 수평 배치
 */
export default function SectionHeader({
    title,
    onMenuClick,
    className = '',
}: SectionHeaderProps) {
    return (
        <div className={`flex items-center justify-between ${className}`}>
            <h2 className="text-xl font-semibold text-gray-800">
                {title}
            </h2>
            {onMenuClick && (
                <MenuButton onClick={onMenuClick} size="medium" />
            )}
        </div>
    );
}
