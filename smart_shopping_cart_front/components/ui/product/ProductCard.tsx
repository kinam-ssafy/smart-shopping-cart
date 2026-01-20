'use client';

import SafeImage from '../../common/SafeImage';
import Rating from '../review/Rating';
import LocationIcon from '../../icons/LocationIcon';

interface ProductCardProps {
    /** 제품 ID */
    id: string;

    /** 제품명 */
    name: string;

    /** 제품 가격 */
    price: number;

    /** 제품 이미지 URL */
    image: string;

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
 * 제품 카드 컴포넌트
 * 가로형 레이아웃 (이미지 좌측 + 정보 우측)
 */
export default function ProductCard({
    id,
    name,
    price,
    image,
    quantity,
    rating,
    location,
    onClick,
    className = '',
}: ProductCardProps) {
    return (
        <div
            onClick={onClick}
            className={`
        flex gap-4
        bg-white
        rounded-[20px]
        shadow-md
        p-4
        transition-all duration-200
        hover:shadow-lg
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
        >
            <div className="relative w-24 h-24 flex-shrink-0 rounded-[12px] overflow-hidden bg-gray-100">
                <SafeImage
                    src={image}
                    alt={name}
                    fill
                    className="object-cover"
                    placeholderSize={32}
                />
            </div>

            {/* 제품 정보 (우측) */}
            <div className="flex-1 flex flex-col justify-between min-w-0">
                {/* 상단: 제품명 */}
                <div className="min-h-[3rem]">
                    <h3 className="font-semibold text-gray-800 text-base line-clamp-2">
                        {name}
                    </h3>
                </div>

                {/* 하단: 위치 + 별점 + 수량/가격 */}
                <div className="space-y-1">
                    {/* 매장 위치 */}
                    {location && (
                        <div className="flex items-center gap-1 text-xs text-gray-600">
                            <LocationIcon size={12} />
                            <span>{location}</span>
                        </div>
                    )}

                    <div className="flex items-end justify-between">
                        {/* 별점 */}
                        <div className="flex-shrink-0">
                            <Rating rating={rating} size={16} />
                        </div>

                        {/* 수량 + 가격 (세로 배치) */}
                        <div className="text-right">
                            <div className="text-sm text-gray-500">
                                Qty: <span className="font-medium text-gray-700">{quantity}</span>
                            </div>
                            <div className="text-lg font-bold text-gray-800">
                                ${price.toFixed(2)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
