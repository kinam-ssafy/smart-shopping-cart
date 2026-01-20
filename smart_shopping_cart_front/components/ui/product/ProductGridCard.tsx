'use client';

import { useState } from 'react';
import SafeImage from '../../common/SafeImage';
import Rating from '../review/Rating';
import LocationIcon from '../../icons/LocationIcon';

interface ProductGridCardProps {
    /** 제품 ID */
    id: string;

    /** 제품명 */
    name: string;

    /** 제품 가격 */
    price: number;

    /** 제품 이미지 URL (단일 또는 배열) */
    image: string | string[];

    /** 제품 수량 */
    quantity: number;

    /** 별점 (0-5) */
    rating: number;

    /** 매장 위치 (예: A-1, B-3) */
    location?: string;

    /** 클릭 핸들러 */
    onClick?: () => void;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 그리드형 제품 카드 컴포넌트
 * 세로형 레이아웃 (이미지 상단 + 정보 하단)
 * 한 줄에 2개씩 배치 가능, 이미지 캐로셀 지원
 */
export default function ProductGridCard({
    id,
    name,
    price,
    image,
    quantity,
    rating,
    location,
    onClick,
    className = '',
}: ProductGridCardProps) {
    const images = Array.isArray(image) ? image : [image];
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const handlePrevImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) =>
            prev === 0 ? images.length - 1 : prev - 1
        );
    };

    const handleNextImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentImageIndex((prev) =>
            prev === images.length - 1 ? 0 : prev + 1
        );
    };

    return (
        <div
            onClick={onClick}
            className={`
        bg-white
        rounded-[20px]
        shadow-md
        overflow-hidden
        transition-all duration-200
        hover:shadow-lg
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
        >
            {/* 제품 이미지 (상단) - 캐로셀 */}
            <div className="relative w-full aspect-[4/3] bg-gray-100">
                <SafeImage
                    src={images[currentImageIndex]}
                    alt={name}
                    fill
                    className="object-cover"
                    placeholderSize={48}
                />

                {/* 캐로셀 컨트롤 (이미지가 2개 이상일 때만) */}
                {images.length > 1 && (
                    <>
                        {/* 이전 버튼 */}
                        <button
                            onClick={handlePrevImage}
                            className="absolute left-1 top-1/2 -translate-y-1/2 w-6 h-6 bg-white/80 rounded-full flex items-center justify-center hover:bg-white transition-colors"
                            aria-label="Previous image"
                        >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                                <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </button>

                        {/* 다음 버튼 */}
                        <button
                            onClick={handleNextImage}
                            className="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 bg-white/80 rounded-full flex items-center justify-center hover:bg-white transition-colors"
                            aria-label="Next image"
                        >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                                <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </button>

                        {/* 인디케이터 */}
                        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                            {images.map((_, index) => (
                                <div
                                    key={index}
                                    className={`w-1.5 h-1.5 rounded-full transition-colors ${index === currentImageIndex ? 'bg-white' : 'bg-white/50'
                                        }`}
                                />
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* 제품 정보 (하단) */}
            <div className="p-3 space-y-1.5">
                {/* 제품명 */}
                <h3 className="font-semibold text-gray-800 text-sm line-clamp-2 min-h-[2.5rem]">
                    {name}
                </h3>

                {/* 매장 위치 */}
                {location && (
                    <div className="flex items-center gap-0.5 text-xs text-gray-600">
                        <LocationIcon size={10} />
                        <span>{location}</span>
                    </div>
                )}

                {/* 별점 */}
                <div>
                    <Rating rating={rating} size={12} />
                </div>

                {/* 수량 + 가격 */}
                <div className="flex items-center justify-between pt-0.5">
                    <div className="text-xs text-gray-500">
                        Left Qty: <span className="font-medium text-gray-700">{quantity}</span>
                    </div>
                    <div className="text-base font-bold text-gray-800">
                        ${price.toFixed(2)}
                    </div>
                </div>
            </div>
        </div>
    );
}
