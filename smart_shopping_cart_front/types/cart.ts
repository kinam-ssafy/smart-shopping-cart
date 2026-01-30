/**
 * 백엔드 API 타입 정의
 */

// 카트 상품 DTO
// 통합 상품 타입 (Backend ProductDto 대응)
export interface Product {
    id: number;
    name: string;
    price: number;
    images: string[];      // Unified to array
    quantity: number;
    rating: number;
    location?: string;
    hasRfid: boolean;
    rfidUid?: string;
    detail?: ProductDetail;
}

// 상품 상세 정보
export interface ProductDetail {
    description: string;
    reviews: Review[];
}

// 리뷰
export interface Review {
    rating: number;
    content: string;
    images?: string[];
}

// Search 기본 응답
export interface SearchDefaultResponse {
    popular: Product[];
    recommended: Product[];
}

// SSE 메시지 타입
export interface CartSseMessage {
    products: Product[];
}

// MQTT 상태 응답
export interface CartStatusResponse {
    mqttConnected: boolean;
    timestamp: string;
}
