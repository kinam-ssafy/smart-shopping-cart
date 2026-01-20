'use client';

import { useState, useRef, useEffect } from 'react';
import ProductCard from './ProductCard';
import ProductDetail from './ProductDetail';

interface ExpandableProductCardProps {
    /** 제품 ID */
    id: string;

    /** 제품명 */
    name: string;

    /** 제품 가격 */
    price: number;

    /** 제품 썸네일 이미지 */
    image: string;

    /** 제품 수량 */
    quantity: number;

    /** 별점 */
    rating: number;

    /** 매장 위치 (예: A-1, B-3) */
    location?: string;

    /** 상세 정보 */
    detail: {
        images: string[];
        description: string;
        averageRating: number;
        reviews: Array<{
            rating: number;
            content: string;
            images?: string[];
        }>;
    };

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 확장 가능한 제품 카드 컴포넌트
 * 클릭 시 상세 정보가 아래로 확장됨
 */
export default function ExpandableProductCard({
    id,
    name,
    price,
    image,
    quantity,
    rating,
    location,
    detail,
    className = '',
}: ExpandableProductCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const detailRef = useRef<HTMLDivElement>(null);

    const handleToggle = () => {
        setIsExpanded(!isExpanded);
    };

    // 확장될 때 스크롤
    useEffect(() => {
        if (isExpanded && detailRef.current) {
            // 약간의 지연 후 스크롤 (애니메이션 시작 후)
            setTimeout(() => {
                detailRef.current?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                });
            }, 100);
        }
    }, [isExpanded]);

    return (
        <div className={className}>
            {/* 제품 카드 */}
            <ProductCard
                id={id}
                name={name}
                price={price}
                image={image}
                quantity={quantity}
                rating={rating}
                location={location}
                onClick={handleToggle}
            />

            {/* 확장 영역 (상세 정보) */}
            <div
                ref={detailRef}
                className={`
          overflow-hidden
          transition-all duration-300 ease-in-out
          ${isExpanded ? 'max-h-[1000px] opacity-100 mt-3' : 'max-h-0 opacity-0'}
        `}
            >
                <ProductDetail
                    images={detail.images}
                    description={detail.description}
                    averageRating={detail.averageRating}
                    reviews={detail.reviews}
                />
            </div>
        </div>
    );
}
