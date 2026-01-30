'use client';

import React, { useState, useRef, useEffect } from 'react';
import { BackButton } from '@/components/ui/buttons/Button';
import SearchInput from '@/components/ui/SearchInput';
import SectionHeader from '@/components/ui/SectionHeader';
import ExpandableProductGridCard, { ExpandedDetail } from '@/components/ui/product/ExpandableProductGridCard';
import { Product, SearchDefaultResponse } from '@/types/cart';

// API Base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function SearchPage() {
    const [expandedCardId, setExpandedCardId] = useState<number | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSection, setSelectedSection] = useState('Recommended');
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const expandedDetailRef = useRef<HTMLDivElement>(null);

    // Data State
    const [recommendedProducts, setRecommendedProducts] = useState<Product[]>([]);
    const [popularProducts, setPopularProducts] = useState<Product[]>([]);
    const [searchResults, setSearchResults] = useState<Product[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const sections = ['Recommended', 'Popular'];

    // 1. 초기 데이터 로드 (추천/인기)
    useEffect(() => {
        const fetchDefaultData = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/search/default`);
                if (!res.ok) throw new Error('Failed to fetch default data');
                const data: SearchDefaultResponse = await res.json();
                setRecommendedProducts(data.recommended);
                setPopularProducts(data.popular);
            } catch (error) {
                console.error('Error fetching default search data:', error);
            }
        };

        fetchDefaultData();
    }, []);

    // 2. 검색 실행
    const handleSearch = async (query: string) => {
        setSearchQuery(query);
        setExpandedCardId(null); // 검색 시 확장 닫기

        if (!query.trim()) {
            setSearchResults([]);
            return;
        }

        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/search?query=${encodeURIComponent(query)}`);
            if (!res.ok) throw new Error('Search failed');
            const data: Product[] = await res.json();
            setSearchResults(data);
        } catch (error) {
            console.error('Search error:', error);
            setSearchResults([]);
        } finally {
            setIsLoading(false);
        }
    };

    // 확장 시 스크롤
    useEffect(() => {
        if (expandedCardId && expandedDetailRef.current) {
            setTimeout(() => {
                expandedDetailRef.current?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                });
            }, 100);
        }
    }, [expandedCardId]);

    const handleSectionChange = (section: string) => {
        setSelectedSection(section);
        setIsMenuOpen(false);
    };

    // 현재 표시할 상품 목록 결정
    const displayProducts = searchQuery
        ? searchResults
        : selectedSection === 'Recommended'
            ? recommendedProducts
            : popularProducts;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* 메인 콘텐츠 영역 */}
            <div className="px-4 py-3">
                {/* 상단: Back 버튼 (좌측 정렬) */}
                <div className="flex justify-start mb-3">
                    <BackButton
                        size="medium"
                        onClick={() => window.location.href = '/cart/1'}
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

                        {/* 드롭다운 메뉴 */}
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

                {/* Loading State */}
                {isLoading && (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
                    </div>
                )}

                {/* Product Grid (2열) */}
                {!isLoading && (
                    <div className="grid grid-cols-2 gap-3 mt-4">
                        {Array.from({ length: Math.ceil(displayProducts.length / 2) }).map((_, rowIndex) => {
                            const startIdx = rowIndex * 2;
                            const rowProducts = displayProducts.slice(startIdx, startIdx + 2);
                            const expandedProductInRow = rowProducts.find(p => expandedCardId === p.id);

                            return (
                                <React.Fragment key={`row-${rowIndex}`}>
                                    {/* 행의 카드들 */}
                                    {rowProducts.map((product) => (
                                        <ExpandableProductGridCard
                                            key={product.id}
                                            id={String(product.id)}
                                            name={product.name}
                                            price={product.price}
                                            image={product.images} // Array passed directly
                                            quantity={product.quantity}
                                            rating={product.rating}
                                            location={product.location}
                                            isExpanded={expandedCardId === product.id}
                                            onToggle={() => setExpandedCardId(expandedCardId === product.id ? null : product.id)}
                                            hasRfid={true} // Forced true as requested
                                        />
                                    ))}

                                    {/* 빈 자리 채우기 (마지막 행이 1개만 있을 때) */}
                                    {rowProducts.length === 1 && <div />}

                                    {/* 확장 영역 */}
                                    {expandedProductInRow && expandedProductInRow.detail && (
                                        <ExpandedDetail
                                            detail={{
                                                images: expandedProductInRow.images, // Use main images
                                                description: expandedProductInRow.detail.description,
                                                averageRating: expandedProductInRow.rating,
                                                reviews: expandedProductInRow.detail.reviews
                                            }}
                                            detailRef={expandedDetailRef}
                                            hasRfid={true} // Forced true as requested
                                            location={expandedProductInRow.location}
                                            onNavigate={() => {
                                                console.log('Navigate to:', expandedProductInRow.location);
                                                // TODO: Implement navigation
                                            }}
                                        />
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>
                )}

                {/* 검색 결과 없음 */}
                {!isLoading && searchQuery && displayProducts.length === 0 && (
                    <div className="text-center py-12">
                        <p className="text-gray-500 text-lg">No products found</p>
                        <p className="text-gray-400 text-sm mt-2">Try searching with different keywords</p>
                    </div>
                )}
            </div>
        </div>
    );
}
