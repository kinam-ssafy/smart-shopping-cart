'use client';

import StarIcon from '../../icons/StarIcon';

interface RatingProps {
    /** 별점 (0-5) */
    rating: number;

    /** 별 크기 */
    size?: number;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 별점 표시 컴포넌트
 * 0-5점 사이의 별점을 표시
 */
export default function Rating({
    rating,
    size = 16,
    className = '',
}: RatingProps) {
    // 별점을 0-5 사이로 제한
    const clampedRating = Math.max(0, Math.min(5, rating));

    return (
        <div className={`flex items-center gap-0.5 ${className}`}>
            {[1, 2, 3, 4, 5].map((star) => (
                <StarIcon
                    key={star}
                    size={size}
                    filled={star <= clampedRating}
                    className={star <= clampedRating ? 'text-yellow-400' : 'text-gray-300'}
                />
            ))}
            <span className="ml-1 text-sm text-gray-600">
                {clampedRating.toFixed(1)}
            </span>
        </div>
    );
}
