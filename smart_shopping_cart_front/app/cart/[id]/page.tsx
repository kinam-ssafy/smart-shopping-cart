'use client';

import { notFound } from 'next/navigation';
import { use, useState, useEffect, useRef } from 'react';
import { SearchButton } from '@/components/ui/buttons/Button';
import StoreMap from '@/components/map/StoreMap';
import ExpandableProductCard from '@/components/ui/product/ExpandableProductCard';
import CartFooter from '@/components/layout/CartFooter';
import { Product, CartSseMessage } from '@/types/cart';

// 백엔드 API URL (환경변수로 설정 가능)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function CartPage({ params }: { params: Promise<{ id: string }> }) {
    const [cartItems, setCartItems] = useState<Product[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [navigationPath, setNavigationPath] = useState<number[][] | null>(null);

    // 이전 장바구니 수량 추적 및 초기 로딩 감지
    const prevCartLength = useRef(0);
    const isFirstLoad = useRef(true);

    // 장바구니 수량 증가 시 효과음 재생
    useEffect(() => {
        if (isFirstLoad.current) {
            isFirstLoad.current = false;
            prevCartLength.current = cartItems.length;
            return;
        }

        if (cartItems.length > prevCartLength.current) {
            const audio = new Audio('/beep.mp3');
            audio.play().catch(e => console.error('[Audio] 재생 실패 (사용자 인터랙션 필요):', e));
        }
        prevCartLength.current = cartItems.length;
    }, [cartItems]);

    // params를 unwrap (Next.js 15 이상)
    const { id: cartId } = use(params);

    // ID 검증: 숫자인지 확인
    const isValidId = /^\d+$/.test(cartId);

    // ID가 숫자가 아니면 404 페이지로
    if (!isValidId) {
        notFound();
    }

    // 1. sessionStorage에서 경로 데이터 읽기
    useEffect(() => {
        const storedPath = sessionStorage.getItem('navigationPath');
        if (storedPath) {
            try {
                const path = JSON.parse(storedPath);
                setNavigationPath(path);
                console.log('[Cart] 경로 로드됨:', path.length, '개 waypoint');
                // 한 번 읽은 후 삭제 (일회성)
                sessionStorage.removeItem('navigationPath');
            } catch (e) {
                console.error('[Cart] 경로 파싱 오류:', e);
            }
        }
    }, []);

    // SSE 연결
    useEffect(() => {
        let eventSource: EventSource | null = null;

        const connectSSE = () => {
            eventSource = new EventSource(`${API_BASE_URL}/api/cart/stream`);

            eventSource.onopen = () => {
                setIsConnected(true);
                setError(null);
                console.log('[SSE] 연결됨');
            };

            eventSource.onmessage = (event) => {
                try {
                    const data: CartSseMessage = JSON.parse(event.data);
                    if (data.products) {
                        setCartItems(data.products);
                        console.log('[SSE] 상품 수신:', data.products.length, '개');
                    }
                } catch (e) {
                    console.error('[SSE] 파싱 오류:', e);
                }
            };

            eventSource.onerror = () => {
                setIsConnected(false);
                setError('연결 끊김. 재연결 시도 중...');
                console.log('[SSE] 연결 오류, 재연결 시도...');

                eventSource?.close();

                // 3초 후 재연결
                setTimeout(connectSSE, 3000);
            };
        };

        connectSSE();

        return () => {
            eventSource?.close();
        };
    }, []);

    // 총액 계산
    const totalAmount = cartItems.reduce(
        (sum, item) => sum + item.price * item.quantity,
        0
    );

    // 경로 초기화 핸들러
    const clearNavigationPath = () => setNavigationPath(null);

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* 메인 콘텐츠 영역 */}
            <div className="flex-1 px-4 py-3">
                {/* 상단: Search 버튼 + 연결 상태 */}
                <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-xs text-gray-500">
                            {isConnected ? '실시간 연결' : '연결 끊김'}
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* 경로 표시 중일 때 닫기 버튼 */}
                        {navigationPath && (
                            <button
                                onClick={clearNavigationPath}
                                className="px-3 py-1.5 text-sm bg-orange-500 text-white rounded-lg"
                            >
                                경로 닫기
                            </button>
                        )}
                        <SearchButton
                            size="medium"
                            onClick={() => window.location.href = '/search'}
                        />
                    </div>
                </div>

                {/* 에러 메시지 */}
                {error && (
                    <div className="text-center text-sm text-orange-600 mb-2">
                        {error}
                    </div>
                )}

                {/* 지도 (정사각형, 축소) */}
                <div className="mb-6 max-w-sm mx-auto">
                    <StoreMap
                        className="w-full aspect-square rounded-2xl"
                        navigationPath={navigationPath}
                    />
                </div>

                {/* 장바구니 상품 리스트 */}
                <div className="mb-6">
                    {/* 장바구니 타이틀 */}
                    <h2 className="text-xl font-bold text-gray-800 mb-4 pl-1">
                        Shopping Basket
                        <span className="text-sm font-normal text-gray-500 ml-2">
                            ({cartItems.length}개)
                        </span>
                    </h2>

                    {cartItems.length === 0 ? (
                        <div className="text-center py-12 text-gray-400">
                            <p className="text-lg mb-2">장바구니가 비어있습니다</p>
                            <p className="text-sm">상품을 카트에 담아주세요</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {cartItems.map((item) => (
                                <ExpandableProductCard
                                    key={item.id}
                                    id={String(item.id)}
                                    name={item.name}
                                    price={item.price}
                                    image={item.images?.[0] || 'https://via.placeholder.com/200'}
                                    quantity={item.quantity}
                                    rating={item.rating}
                                    location={item.location}
                                    detail={item.detail ? {
                                        images: item.images, // Use main images or detail images? usually Detail should have images but backend ProductDto separated them. Backend ProductDto has Images on root. ProductDetailDto has no Images. Wait.
                                        description: item.detail.description,
                                        averageRating: item.rating, // ProductDto rating is average
                                        reviews: item.detail.reviews.map(r => ({
                                            rating: r.rating,
                                            content: r.content,
                                            images: r.images
                                        }))
                                    } : {
                                        images: [],
                                        description: '',
                                        averageRating: 0,
                                        reviews: []
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 하단: Cart Footer (sticky) */}
            <div className="sticky bottom-0">
                <CartFooter totalAmount={totalAmount} />
            </div>
        </div>
    );
}
