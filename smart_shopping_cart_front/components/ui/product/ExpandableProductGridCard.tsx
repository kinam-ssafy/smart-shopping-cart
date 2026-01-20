'use client';

import { useRef, useEffect } from 'react';
import ProductGridCard from './ProductGridCard';
import ProductDetail from './ProductDetail';

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

    /** 확장 상태 (외부에서 제어) */
    isExpanded: boolean;

    /** 확장 토글 핸들러 */
    onToggle: () => void;

    /** 그리드 내 위치 (행 번호 계산용) */
    index: number;

    /** 추가 CSS 클래스 */
    className?: string;
}

/**
 * 확장 가능한 그리드형 제품 카드 컴포넌트
 * 클릭 시 상세 정보가 그리드 전체 너비로 확장되며, 선택된 카드는 시각적으로 강조됨
 * 확장 시 같은 행의 다른 카드들은 위치 유지
 */
export default function ExpandableProductGridCard({
    id,
    name,
    price,
    image,
    quantity,
    rating,
    location,
    detail,
    isExpanded,
    onToggle,
    index,
    className = '',
}: ExpandableProductGridCardProps) {
    const detailRef = useRef<HTMLDivElement>(null);

    // 확장될 때 스크롤
    useEffect(() => {
        if (isExpanded && detailRef.current) {
            setTimeout(() => {
                detailRef.current?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                });
            }, 100);
        }
    }, [isExpanded]);

    // 2열 그리드에서 행 번호 계산 (0-based)
    const rowIndex = Math.floor(index / 2);

    // 확장 영역의 grid-row 위치: 카드가 있는 행의 다음 행
    const detailRowStart = rowIndex * 2 + 2; // 카드 행 + 확장 행

    return (
        <>
            {/* 제품 카드 - 선택 시 테두리 강조 */}
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

            {/* 확장 영역 (상세 정보) - 그리드 전체 너비 차지, 같은 행 다음에 배치 */}
            {isExpanded && (
                <div
                    ref={detailRef}
                    className="col-span-2"
                    style={{
                        gridColumn: '1 / -1',
                        gridRow: detailRowStart,
                    }}
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
            )}
        </>
    );
}
