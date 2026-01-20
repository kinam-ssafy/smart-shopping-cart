interface IconProps {
    size?: number;
    className?: string;
}

/**
 * 이미지 플레이스홀더 아이콘
 * 이미지 로드 실패 시 표시
 */
export default function ImagePlaceholderIcon({ size = 48, className = '' }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            className={className}
        >
            {/* 외곽 사각형 */}
            <rect
                x="3"
                y="3"
                width="18"
                height="18"
                rx="2"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />

            {/* 태양/원 */}
            <circle
                cx="8.5"
                cy="8.5"
                r="1.5"
                fill="currentColor"
            />

            {/* 산 모양 */}
            <path
                d="M21 15l-3.086-3.086a2 2 0 00-2.828 0L6 21"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}
