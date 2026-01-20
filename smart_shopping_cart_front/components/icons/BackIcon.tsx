interface IconProps {
    size?: number;
    className?: string;
}

/**
 * 뒤로가기 아이콘 (왼쪽 화살표)
 */
export default function BackIcon({ size = 24, className = '' }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 12 21"
            fill="none"
            className={className}
        >
            <path
                d="M10.085 18.585L1.58502 10.085L10.085 1.58499"
                stroke="currentColor"
                strokeWidth={3.17}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}
