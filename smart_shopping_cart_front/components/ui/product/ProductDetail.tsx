'use client';

import { useState } from 'react';
import SafeImage from '../../common/SafeImage';
import Rating from '../review/Rating';
import Review from '../review/Review';

interface ProductDetailProps {
    /** 제품 이미지 URL 배열 */
    images: string[];

    /** 제품 상세 설명 */
    description: string;

    /** 전체 별점 평균 */
    averageRating: number;

    /** 리뷰 목록 */
    reviews: Array<{
        rating: number;
        content: string;
        images?: string[];
    }>;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 확장형 상품 상세보기 컴포넌트
 * 이미지 캐로셀, 상세 설명, 별점, 리뷰 포함
 */
export default function ProductDetail({
    images,
    description,
    averageRating,
    reviews,
    className = '',
}: ProductDetailProps) {
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
        <div className={`bg-white rounded-lg p-4 space-y-4 ${className}`}>
            {/* 이미지 캐로셀 */}
            <div className="relative">
                <div className="relative w-full h-48 rounded-lg overflow-hidden bg-gray-200">
                    <SafeImage
                        src={images[currentImageIndex]}
                        alt={`Product image ${currentImageIndex + 1}`}
                        fill
                        className="object-cover"
                        placeholderSize={64}
                    />
                </div>

                {/* 캐로셀 컨트롤 (이미지가 2개 이상일 때만) */}
                {images.length > 1 && (
                    <>
                        {/* 이전 버튼 */}
                        <button
                            onClick={handlePrevImage}
                            className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center hover:bg-white transition-colors shadow-md"
                            aria-label="Previous image"
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </button>

                        {/* 다음 버튼 */}
                        <button
                            onClick={handleNextImage}
                            className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center hover:bg-white transition-colors shadow-md"
                            aria-label="Next image"
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </button>

                        {/* 인디케이터 */}
                        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                            {images.map((_, index) => (
                                <div
                                    key={index}
                                    className={`w-2 h-2 rounded-full transition-colors ${index === currentImageIndex ? 'bg-white' : 'bg-white/50'
                                        }`}
                                />
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* 상세 설명 */}
            <div className="border-t border-gray-200 pt-4">
                <h3 className="font-semibold text-gray-800 mb-2">Description</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                    {description}
                </p>
            </div>

            {/* 전체 별점 */}
            <div className="border-t border-gray-200 pt-4">
                <h3 className="font-semibold text-gray-800 mb-2">Rating</h3>
                <div className="flex items-center gap-2">
                    <Rating rating={averageRating} size={16} />
                    <span className="text-sm text-gray-500">
                        ({reviews.length} {reviews.length === 1 ? 'review' : 'reviews'})
                    </span>
                </div>
            </div>

            {/* 리뷰 목록 */}
            {reviews.length > 0 && (
                <div className="border-t border-gray-200 pt-4">
                    <h3 className="font-semibold text-gray-800 mb-3">Reviews</h3>
                    <div className="space-y-2">
                        {reviews.slice(0, 3).map((review, index) => (
                            <Review
                                key={index}
                                rating={review.rating}
                                content={review.content}
                                images={review.images}
                            />
                        ))}
                    </div>
                    {reviews.length > 3 && (
                        <p className="text-xs text-gray-500 text-center mt-3">
                            +{reviews.length - 3} more {reviews.length - 3 === 1 ? 'review' : 'reviews'}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
