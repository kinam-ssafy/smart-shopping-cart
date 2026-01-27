'use client';

import { useRef, useEffect } from 'react';
import ProductGridCard from './ProductGridCard';
import ProductDetail from './ProductDetail';

export interface ProductDetailType {
    images: string[];
    description: string;
    averageRating: number;
    reviews: Array<{
        rating: number;
        content: string;
        images?: string[];
    }>;
}

interface ExpandableProductGridCardProps {
    /** 제품 ID */
    id: string;

    /** 제품명 */
    name: string;

    /** 제품 가격 */
    price: number;

    /** 제품 썸네일 이미지 (단일 또는 배열) */
    image: string | string[];

    /** 제품 수량 */
    quantity: number;

    /** 별점 */
    rating: number;

    /** 매장 위치 (예: A-1, B-3) */
    location?: string;

    /** 확장 상태 (외부에서 제어) */
    isExpanded: boolean;

    /** 확장 토글 핸들러 */
    onToggle: () => void;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 확장 가능한 그리드형 제품 카드 컴포넌트 (카드 부분만)
 * 클릭 시 선택 상태가 시각적으로 강조됨
 * 확장 영역은 부모 컴포넌트에서 별도로 렌더링해야 함
 */
export default function ExpandableProductGridCard({
    id,
    name,
    price,
    image,
    quantity,
    rating,
    location,
    isExpanded,
    onToggle,
    className = '',
}: ExpandableProductGridCardProps) {
    return (
        <div className={className}>
            <div className={`
                transition-all duration-200
                ${isExpanded ? 'ring-2 ring-blue-500 ring-offset-2 rounded-[22px]' : ''}
            `}>
                <ProductGridCard
                    id={id}
                    name={name}
                    price={price}
                    image={image}
                    quantity={quantity}
                    rating={rating}
                    location={location}
                    onClick={onToggle}
                />
            </div>
        </div>
    );
}

interface ExpandedDetailProps {
    detail: ProductDetailType;
    detailRef?: React.RefObject<HTMLDivElement | null>;
}

/**
 * 확장된 상세 정보 컴포넌트
 * 그리드의 전체 너비를 차지하며, 행 단위로 렌더링됨
 */
export function ExpandedDetail({ detail, detailRef }: ExpandedDetailProps) {
    return (
        <div
            ref={detailRef}
            className="col-span-2"
        >
            <div className="mt-3 animate-in fade-in slide-in-from-top-2 duration-300">
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
