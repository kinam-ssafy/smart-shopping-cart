/**
 * 백엔드 API 타입 정의
 */

// 카트 상품 DTO
export interface CartProduct {
    id: number;
    name: string;
    price: number;
    image?: string;
    quantity: number;
    rating: number;
    location?: string;
    hasRfid: boolean;
    rfidUid?: string;
    detail?: CartProductDetail;
}

// 상품 상세 정보
export interface CartProductDetail {
    images: string[];
    description: string;
    averageRating: number;
    reviews: Review[];
}

// 리뷰
export interface Review {
    rating: number;
    content: string;
    images?: string[];
}

// SSE 메시지 타입
export interface CartSseMessage {
    products: CartProduct[];
}

// MQTT 상태 응답
export interface CartStatusResponse {
    mqttConnected: boolean;
    timestamp: string;
}
