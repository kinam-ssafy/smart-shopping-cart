'use client';

import { useState } from 'react';
import { SearchButton, BackButton, MenuButton } from '@/components/ui/buttons/Button';
import SearchInput from '@/components/ui/SearchInput';
import SectionHeader from '@/components/ui/SectionHeader';
import LikeButton from '@/components/ui/buttons/LikeButton';
import ProductCard from '@/components/ui/product/ProductCard';
import ProductGridCard from '@/components/ui/product/ProductGridCard';
import Review from '@/components/ui/review/Review';
import Rating from '@/components/ui/review/Rating';
import ExpandableProductCard from '@/components/ui/product/ExpandableProductCard';
import ExpandableProductGridCard from '@/components/ui/product/ExpandableProductGridCard';
import LocationIcon from '@/components/icons/LocationIcon';
import CartFooter from '@/components/layout/CartFooter';
import StoreMap from '@/components/map/StoreMap';

export default function UIKitPage() {
    const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

    return (
        <div className="min-h-screen bg-white p-6">
            {/* 헤더 */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                    UI Components
                </h1>
                <p className="text-gray-600 text-sm">
                    Project component library
                </p>
            </div>

            {/* Icon Buttons */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Icon Buttons
                </h2>
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h3 className="font-medium text-gray-700 mb-3">Button Types</h3>
                    <div className="flex gap-4 items-center justify-center">
                        <div className="text-center">
                            <SearchButton onClick={() => alert('Search!')} />
                            <p className="text-xs text-gray-500 mt-2">Search</p>
                        </div>
                        <div className="text-center">
                            <BackButton onClick={() => alert('Back!')} />
                            <p className="text-xs text-gray-500 mt-2">Back</p>
                        </div>
                        <div className="text-center">
                            <MenuButton onClick={() => alert('Menu!')} />
                            <p className="text-xs text-gray-500 mt-2">Menu</p>
                        </div>
                        <div className="text-center">
                            <div className="w-10 h-10 flex items-center justify-center bg-white rounded-lg">
                                <LocationIcon size={16} />
                            </div>
                            <p className="text-xs text-gray-500 mt-2">Location</p>
                        </div>
                    </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-700 mb-3">Button Sizes</h3>
                    <div className="flex gap-4 items-center justify-center">
                        <div className="text-center">
                            <SearchButton size="small" />
                            <p className="text-xs text-gray-500 mt-2">Small</p>
                        </div>
                        <div className="text-center">
                            <SearchButton size="medium" />
                            <p className="text-xs text-gray-500 mt-2">Medium</p>
                        </div>
                        <div className="text-center">
                            <SearchButton size="large" />
                            <p className="text-xs text-gray-500 mt-2">Large</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Search Input */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Search Input
                </h2>
                <div className="bg-gray-50 rounded-lg p-4">
                    <SearchInput
                        placeholder="Search..."
                        onSearch={(value) => alert(`Search: ${value}`)}
                    />
                </div>
            </section>

            {/* Like Button */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Like Button
                </h2>
                <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex gap-6 items-center justify-center">
                        <div className="text-center">
                            <LikeButton initialCount={0} />
                            <p className="text-xs text-gray-500 mt-2">Not Liked</p>
                        </div>
                        <div className="text-center">
                            <LikeButton initialCount={42} initialLiked />
                            <p className="text-xs text-gray-500 mt-2">Liked</p>
                        </div>
                        <div className="text-center">
                            <LikeButton initialCount={128} />
                            <p className="text-xs text-gray-500 mt-2">Interactive</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Rating */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Rating
                </h2>
                <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex gap-6 items-center justify-center">
                        <Rating rating={5.0} />
                        <Rating rating={4.5} />
                        <Rating rating={3.0} />
                        <Rating rating={1.5} />
                    </div>
                </div>
            </section>

            {/* Section Header */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Section Header
                </h2>
                <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                    <SectionHeader
                        title="Recommended"
                        onMenuClick={() => alert('Menu clicked')}
                    />
                    <SectionHeader
                        title="Popular"
                        onMenuClick={() => alert('Menu clicked')}
                    />
                </div>
            </section>

            {/* Product Card */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Product Card
                </h2>
                <div className="space-y-3">
                    <ProductCard
                        id="1"
                        name="Fresh Organic Apples"
                        price={4.99}
                        image="https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=200&h=200&fit=crop"
                        quantity={3}
                        rating={4.5}
                        location="A-1"
                        onClick={() => alert('Product clicked!')}
                    />
                    <ProductCard
                        id="2"
                        name="Premium Chocolate Bar with Nuts and Caramel"
                        price={12.50}
                        image="https://images.unsplash.com/photo-1606312619070-d48b4ceb6b3d?w=200&h=200&fit=crop"
                        quantity={1}
                        rating={4.8}
                        location="B-3"
                        onClick={() => alert('Product clicked!')}
                    />
                </div>
            </section>

            {/* Product Grid Card */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Product Grid Card
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                    Vertical layout for grid display (2 cards per row)
                </p>
                <div className="grid grid-cols-2 gap-3">
                    <ProductGridCard
                        id="1"
                        name="Fresh Organic Apples"
                        price={4.99}
                        image={[
                            "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=300&h=300&fit=crop",
                            "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
                            "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=300&h=300&fit=crop"
                        ]}
                        quantity={3}
                        rating={4.5}
                        location="A-1"
                        onClick={() => alert('Product clicked!')}
                    />
                    <ProductGridCard
                        id="2"
                        name="Premium Chocolate Bar"
                        price={12.50}
                        image="https://images.unsplash.com/photo-1606312619070-d48b4ceb6b3d?w=300&h=300&fit=crop"
                        quantity={1}
                        rating={4.8}
                        location="B-3"
                        onClick={() => alert('Product clicked!')}
                    />
                    <ProductGridCard
                        id="3"
                        name="Organic Whole Milk"
                        price={3.49}
                        image={[
                            "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&h=300&fit=crop",
                            "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop"
                        ]}
                        quantity={2}
                        rating={4.2}
                        location="C-2"
                        onClick={() => alert('Product clicked!')}
                    />
                    <ProductGridCard
                        id="4"
                        name="Artisan Sourdough Bread"
                        price={5.99}
                        image="https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop"
                        quantity={1}
                        rating={4.9}
                        location="D-5"
                        onClick={() => alert('Product clicked!')}
                    />
                </div>
            </section>

            {/* Expandable Product Grid Card */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Expandable Product Grid Card
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                    Click on a card to expand details (selected card shows blue ring)
                </p>
                <div className="grid grid-cols-2 gap-3">
                    <ExpandableProductGridCard
                        id="1"
                        name="Fresh Organic Apples"
                        price={4.99}
                        image={[
                            "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=300&h=300&fit=crop",
                            "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop"
                        ]}
                        quantity={3}
                        rating={4.5}
                        location="A-1"
                        index={0}
                        isExpanded={expandedCardId === '1'}
                        onToggle={() => setExpandedCardId(expandedCardId === '1' ? null : '1')}
                        detail={{
                            images: [
                                "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400&h=300&fit=crop",
                                "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=300&fit=crop",
                                "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=300&fit=crop"
                            ],
                            description: "Fresh, crisp, and delicious organic apples from local farms. Perfect for snacking, baking, or making fresh juice.",
                            averageRating: 4.5,
                            reviews: [
                                {
                                    rating: 5.0,
                                    content: "Amazing quality! Very fresh and tasty.",
                                    images: ["https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&h=300&fit=crop"]
                                },
                                {
                                    rating: 4.5,
                                    content: "Great apples, my family loves them!",
                                }
                            ]
                        }}
                    />
                    <ExpandableProductGridCard
                        id="2"
                        name="Premium Chocolate Bar"
                        price={12.50}
                        image="https://images.unsplash.com/photo-1606312619070-d48b4ceb6b3d?w=300&h=300&fit=crop"
                        quantity={1}
                        rating={4.8}
                        location="B-3"
                        index={1}
                        isExpanded={expandedCardId === '2'}
                        onToggle={() => setExpandedCardId(expandedCardId === '2' ? null : '2')}
                        detail={{
                            images: [
                                "https://images.unsplash.com/photo-1606312619070-d48b4ceb6b3d?w=400&h=300&fit=crop"
                            ],
                            description: "Premium dark chocolate with nuts and caramel. Made with the finest ingredients.",
                            averageRating: 4.8,
                            reviews: [
                                {
                                    rating: 5.0,
                                    content: "Best chocolate ever!",
                                }
                            ]
                        }}
                    />
                </div>
            </section>

            {/* Review */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Review
                </h2>
                <div className="space-y-3">
                    <Review
                        rating={4.5}
                        content="Great product! Fresh and delicious. Highly recommended for anyone looking for quality organic produce."
                        images={[
                            "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&h=300&fit=crop",
                            "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=300&fit=crop",
                            "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=300&fit=crop"
                        ]}
                    />
                    <Review
                        rating={5.0}
                        content="Perfect! Exactly what I was looking for. The quality exceeded my expectations."
                    />
                </div>
            </section>

            {/* Expandable Product Card */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Expandable Product Card
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                    Click on the card to expand and see product details
                </p>
                <div className="space-y-3">
                    <ExpandableProductCard
                        id="1"
                        name="Fresh Organic Apples"
                        price={4.99}
                        image="https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=200&h=200&fit=crop"
                        quantity={3}
                        rating={4.5}
                        detail={{
                            images: [
                                "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400&h=300&fit=crop",
                                "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=300&fit=crop",
                                "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=300&fit=crop"
                            ],
                            description: "Fresh, crisp, and delicious organic apples from local farms. Perfect for snacking, baking, or making fresh juice. Rich in vitamins and fiber.",
                            averageRating: 4.5,
                            reviews: [
                                {
                                    rating: 5.0,
                                    content: "Amazing quality! Very fresh and tasty.",
                                    images: ["https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&h=300&fit=crop"]
                                },
                                {
                                    rating: 4.5,
                                    content: "Great apples, my family loves them!",
                                },
                                {
                                    rating: 4.0,
                                    content: "Good quality, will buy again.",
                                }
                            ]
                        }}
                    />
                </div>
            </section>

            {/* Cart Footer */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Cart Footer
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                    Footer component displaying cart total (full width, no horizontal padding)
                </p>
                <div className="bg-gray-100 rounded-lg overflow-hidden">
                    <div className="h-40 flex items-end">
                        <CartFooter totalAmount={127.48} />
                    </div>
                </div>
            </section>

            {/* Store Map (3D) */}
            <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Store Map (3D)
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                    Three.js based 3D store layout with product locations (drag to rotate, scroll to zoom)
                </p>
                <StoreMap />
            </section>
        </div>
    );
}
