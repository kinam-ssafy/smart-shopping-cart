'use client';

import { useState } from 'react';
import { BackButton } from '@/components/ui/buttons/Button';
import SearchInput from '@/components/ui/SearchInput';
import SectionHeader from '@/components/ui/SectionHeader';
import ExpandableProductGridCard from '@/components/ui/product/ExpandableProductGridCard';

// 목데이터: 추천 상품들
const MOCK_RECOMMENDED_PRODUCTS = [
    {
        id: '1',
        name: 'Fresh Organic Apples',
        price: 4.99,
        image: [
            'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=300&h=300&fit=crop',
            'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop',
        ],
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
        name: 'Premium Chocolate Bar',
        price: 12.50,
        image: 'https://images.unsplash.com/photo-1606312619070-d48b4ceb6b3d?w=300&h=300&fit=crop',
        quantity: 1,
        rating: 4.8,
        location: 'B-3',
        detail: {
            images: ['https://images.unsplash.com/photo-1606312619070-d48b4ceb6b3d?w=400&h=300&fit=crop'],
            description: 'Rich, smooth premium chocolate with nuts and caramel.',
            averageRating: 4.8,
            reviews: [
                { rating: 5, content: 'Absolutely delicious!' },
            ]
        }
    },
    {
        id: '3',
        name: 'Organic Whole Milk',
        price: 3.49,
        image: [
            'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&h=300&fit=crop',
            'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop',
        ],
        quantity: 2,
        rating: 4.2,
        location: 'C-2',
        detail: {
            images: [
                'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=300&fit=crop',
            ],
            description: 'Fresh whole milk, rich in calcium and vitamins.',
            averageRating: 4.2,
            reviews: [
                { rating: 4, content: 'Great quality milk!' },
            ]
        }
    },
    {
        id: '4',
        name: 'Artisan Sourdough Bread',
        price: 5.99,
        image: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',
        quantity: 1,
        rating: 4.9,
        location: 'D-5',
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
    {
        id: '5',
        name: 'Fresh Orange Juice',
        price: 6.99,
        image: 'https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=300&h=300&fit=crop',
        quantity: 2,
        rating: 4.6,
        location: 'C-4',
        detail: {
            images: ['https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=400&h=300&fit=crop'],
            description: 'Freshly squeezed orange juice, packed with vitamin C.',
            averageRating: 4.6,
            reviews: [
                { rating: 5, content: 'So refreshing!' },
                { rating: 4, content: 'Tastes great!' },
            ]
        }
    },
    {
        id: '6',
        name: 'Crispy Potato Chips',
        price: 3.99,
        image: 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=300&h=300&fit=crop',
        quantity: 1,
        rating: 4.3,
        location: 'D-1',
        detail: {
            images: ['https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&h=300&fit=crop'],
            description: 'Crispy, golden potato chips. Perfect for snacking.',
            averageRating: 4.3,
            reviews: [
                { rating: 4, content: 'Very crunchy!' },
            ]
        }
    },
];

export default function SearchPage() {
    const [expandedCardId, setExpandedCardId] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSection, setSelectedSection] = useState('Recommended');
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const sections = ['Recommended', 'Popular'];

    const handleSearch = (query: string) => {
        setSearchQuery(query);
    };

    const handleSectionChange = (section: string) => {
        setSelectedSection(section);
        setIsMenuOpen(false);
    };

    // 검색어로 상품 필터링
    const filteredProducts = searchQuery
        ? MOCK_RECOMMENDED_PRODUCTS.filter(product =>
            product.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : MOCK_RECOMMENDED_PRODUCTS;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* 메인 콘텐츠 영역 */}
            <div className="px-4 py-3">
                {/* 상단: Back 버튼 (좌측 정렬) */}
                <div className="flex justify-start mb-3">
                    <BackButton
                        size="medium"
                        onClick={() => window.location.href = '/cart'}
                    />
                </div>

                {/* Search Input */}
                <div className="mb-6">
                    <SearchInput
                        placeholder="Search products..."
                        onSearch={handleSearch}
                    />
                </div>

                {/* 검색 중이 아닐 때만 Section Header 표시 */}
                {!searchQuery && (
                    <>
                        {/* Section Header */}
                        <SectionHeader
                            title={selectedSection}
                            onMenuClick={() => setIsMenuOpen(!isMenuOpen)}
                        />

                        {/* 드롭다운 메뉴 (아코디언 스타일) */}
                        <div className={`
                            overflow-hidden transition-all duration-300 ease-in-out
                            ${isMenuOpen ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}
                        `}>
                            <div className="py-2">
                                {sections
                                    .filter(section => section !== selectedSection)
                                    .map((section) => (
                                        <button
                                            key={section}
                                            onClick={() => handleSectionChange(section)}
                                            className="
                                                w-full text-left px-4 py-2
                                                text-gray-600 hover:text-gray-900
                                                transition-colors duration-150
                                            "
                                        >
                                            {section}
                                        </button>
                                    ))
                                }
                            </div>
                        </div>
                    </>
                )}

                {/* 검색 결과 헤더 */}
                {searchQuery && (
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                        Search results for "{searchQuery}"
                    </h3>
                )}

                {/* Product Grid (2열) */}
                <div className="grid grid-cols-2 gap-3 mt-4">
                    {filteredProducts.map((product, index) => (
                        <ExpandableProductGridCard
                            key={product.id}
                            id={product.id}
                            name={product.name}
                            price={product.price}
                            image={product.image}
                            quantity={product.quantity}
                            rating={product.rating}
                            location={product.location}
                            detail={product.detail}
                            index={index}
                            isExpanded={expandedCardId === product.id}
                            onToggle={() => setExpandedCardId(expandedCardId === product.id ? null : product.id)}
                        />
                    ))}
                </div>

                {/* 검색 결과 없음 */}
                {searchQuery && filteredProducts.length === 0 && (
                    <div className="text-center py-12">
                        <p className="text-gray-500 text-lg">No products found</p>
                        <p className="text-gray-400 text-sm mt-2">Try searching with different keywords</p>
                    </div>
                )}
            </div>
        </div>
    );
}
