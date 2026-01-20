'use client';

import { useState } from 'react';
import Image, { ImageProps } from 'next/image';
import ImagePlaceholderIcon from '../icons/ImagePlaceholderIcon';

interface SafeImageProps extends ImageProps {
    /** 플레이스홀더 아이콘 크기 */
    placeholderSize?: number;
}

/**
 * 이미지 로드 실패 시 자동으로 플레이스홀더를 표시하는 안전한 Image 컴포넌트
 * Next.js Image 컴포넌트의 모든 props를 지원하며, 추가로 placeholderSize를 설정할 수 있습니다.
 */
export default function SafeImage({
    placeholderSize = 48,
    ...props
}: SafeImageProps) {
    const [error, setError] = useState(false);

    if (error) {
        return (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                <ImagePlaceholderIcon size={placeholderSize} className="text-gray-400" />
            </div>
        );
    }

    return (
        <Image
            {...props}
            onError={(e) => {
                setError(true);
                // 원래 onError 핸들러가 있으면 호출
                if (props.onError) {
                    props.onError(e);
                }
            }}
        />
    );
}
