interface IconProps {
    size?: number;
    className?: string;
}

/**
 * 햄버거 메뉴 아이콘 (3줄)
 */
export default function MenuIcon({ size = 24, className = '' }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 21 21"
            fill="none"
            className={className}
        >
            <path
                d="M2.61877 10.0915H18.3318"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <path
                d="M2.61877 5.04576H18.3318"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <path
                d="M2.61877 15.1373H18.3318"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}
