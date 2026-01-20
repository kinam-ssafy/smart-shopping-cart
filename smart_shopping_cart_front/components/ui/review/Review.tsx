'use client';

import { useState } from 'react';
import SafeImage from '../../common/SafeImage';
import Rating from './Rating';

interface ReviewProps {
    /** 리뷰 내용 */
    content: string;

    /** 별점 (0-5) */
    rating: number;

    /** 리뷰 이미지 URL 배열 */
    images?: string[];

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 간략한 리뷰 컴포넌트
 * 리뷰 내용, 별점, 이미지 캐로셀 포함
 */
export default function Review({
    content,
    rating,
    images = [],
    className = '',
}: ReviewProps) {
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const handlePrevImage = () => {
        setCurrentImageIndex((prev) =>
            prev === 0 ? images.length - 1 : prev - 1
        );
    };

    const handleNextImage = () => {
        setCurrentImageIndex((prev) =>
            prev === images.length - 1 ? 0 : prev + 1
        );
    };

    return (
        <div className={`bg-gray-50 rounded-lg p-4 flex gap-4 ${className}`}>
            {/* 이미지 캐로셀 (좌측) */}
            {images.length > 0 && (
                <div className="relative flex-shrink-0 w-24">
                    {/* 이미지 */}
                    <div className="relative w-24 h-24 rounded-lg overflow-hidden bg-gray-200">
                        <SafeImage
                            src={images[currentImageIndex]}
                            alt={`Review image ${currentImageIndex + 1}`}
                            fill
                            className="object-cover"
                            placeholderSize={32}
                        />
                    </div>

                    {/* 캐로셀 컨트롤 (이미지가 2개 이상일 때만) */}
                    {images.length > 1 && (
                        <>
                            {/* 이전 버튼 */}
                            <button
                                onClick={handlePrevImage}
                                className="absolute left-1 top-1/2 -translate-y-1/2 w-5 h-5 bg-white/80 rounded-full flex items-center justify-center hover:bg-white transition-colors"
                                aria-label="Previous image"
                            >
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                                    <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>

                            {/* 다음 버튼 */}
                            <button
                                onClick={handleNextImage}
                                className="absolute right-1 top-1/2 -translate-y-1/2 w-5 h-5 bg-white/80 rounded-full flex items-center justify-center hover:bg-white transition-colors"
                                aria-label="Next image"
                            >
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                                    <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>

                            {/* 인디케이터 */}
                            <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
                                {images.map((_, index) => (
                                    <div
                                        key={index}
                                        className={`w-1 h-1 rounded-full transition-colors ${index === currentImageIndex ? 'bg-white' : 'bg-white/50'
                                            }`}
                                    />
                                ))}
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* 리뷰 내용 (우측) */}
            <div className="flex-1 min-w-0">
                {/* 별점 */}
                <div className="mb-2">
                    <Rating rating={rating} size={14} />
                </div>

                {/* 리뷰 내용 */}
                <p className="text-sm text-gray-700 line-clamp-3">
                    {content}
                </p>
            </div>
        </div>
    );
}
