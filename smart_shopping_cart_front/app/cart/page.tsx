'use client';

import { useState } from 'react';
import { SearchButton } from '@/components/ui/buttons/Button';
import StoreMap from '@/components/map/StoreMap';
import ExpandableProductCard from '@/components/ui/product/ExpandableProductCard';
import CartFooter from '@/components/layout/CartFooter';

// 목데이터: 장바구니 상품들
const MOCK_CART_ITEMS = [
    {
        id: '1',
        name: 'Fresh Organic Apples',
        price: 4.99,
        image: 'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=200&h=200&fit=crop',
        quantity: 3,
        rating: 4.5,
        location: 'A-1',
        detail: {
            images: [
                'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=300&fit=crop',
            ],
            description: 'Fresh, crispy organic apples from local farms. Perfect for snacking or baking.',
            averageRating: 4.5,
            reviews: [
                { rating: 5, content: 'Best apples I\'ve ever tasted!' },
                { rating: 4, content: 'Very fresh and crispy.' },
            ]
        }
    },
    {
        id: '2',
        name: 'Whole Milk',
        price: 3.49,
        image: 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=200&h=200&fit=crop',
        quantity: 2,
        rating: 4.8,
        location: 'A-4',
        detail: {
            images: ['https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop'],
            description: 'Fresh whole milk, rich in calcium and vitamins.',
            averageRating: 4.8,
            reviews: [
                { rating: 5, content: 'Great quality milk!' },
            ]
        }
    },
    {
        id: '3',
        name: 'Artisan Sourdough Bread',
        price: 5.99,
        image: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=200&h=200&fit=crop',
        quantity: 1,
        rating: 4.9,
        location: 'C-1',
        detail: {
            images: ['https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop'],
            description: 'Handcrafted sourdough bread with a crispy crust and soft interior.',
            averageRating: 4.9,
            reviews: [
                { rating: 5, content: 'Amazing bread!' },
                { rating: 5, content: 'Best sourdough in town.' },
            ]
        }
    },
];

export default function CartPage() {
    const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

    // 총액 계산
    const totalAmount = MOCK_CART_ITEMS.reduce(
        (sum, item) => sum + item.price * item.quantity,
        0
    );

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* 메인 콘텐츠 영역 */}
            <div className="flex-1 px-4 py-3">
                {/* 상단: Search 버튼 (우측 정렬) */}
                <div className="flex justify-end mb-3">
                    <SearchButton
                        size="medium"
                        onClick={() => window.location.href = '/search'}
                    />
                </div>

                {/* 지도 (정사각형, 축소) */}
                <div className="mb-6 max-w-sm mx-auto">
                    <StoreMap className="w-full aspect-square rounded-2xl" />
                </div>

                {/* 장바구니 상품 리스트 */}
                <div className="space-y-3 mb-6">
                    {MOCK_CART_ITEMS.map((item) => (
                        <ExpandableProductCard
                            key={item.id}
                            id={item.id}
                            name={item.name}
                            price={item.price}
                            image={item.image}
                            quantity={item.quantity}
                            rating={item.rating}
                            location={item.location}
                            detail={item.detail}
                        />
                    ))}
                </div>
            </div>

            {/* 하단: Cart Footer (sticky) */}
            <div className="sticky bottom-0">
                <CartFooter totalAmount={totalAmount} />
            </div>
        </div>
    );
}
