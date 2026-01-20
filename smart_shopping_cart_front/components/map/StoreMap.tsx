'use client';

import { useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Text } from '@react-three/drei';
import * as THREE from 'three';

interface ProductLocation {
    id: string;
    position: string; // "A-1", "B-3" 등
    coordinates: { x: number; y: number; z: number };
    productName?: string;
    category?: string;
}

interface StoreLayout {
    /** 매장 그리드 크기 (행 x 열) */
    gridSize: { rows: number; cols: number };

    /** 선반 간격 */
    shelfSpacing: { x: number; z: number };

    /** 섹션 정의 (선택적) */
    sections?: Array<{
        name: string;
        color: string;
        positions: string[]; // ["A-1", "A-2", ...]
    }>;
}

interface StoreMapProps {
    /** 상품 위치 데이터 */
    locations?: ProductLocation[];

    /** 매장 레이아웃 설정 */
    layout?: StoreLayout;

    /** 사용자(카트) 현재 위치 */
    userPosition?: { x: number; y: number; z: number };

    /** 추가 CSS 클래스 */
    className?: string;
}

// 기본 레이아웃 설정
const DEFAULT_LAYOUT: StoreLayout = {
    gridSize: { rows: 4, cols: 6 },
    shelfSpacing: { x: 2.5, z: 2.5 },
    sections: [
        {
            name: 'Fruits & Vegetables',
            color: '#4CAF50',
            positions: ['A-1', 'A-2', 'A-3', 'B-1', 'B-2', 'B-3']
        },
        {
            name: 'Dairy & Eggs',
            color: '#2196F3',
            positions: ['A-4', 'A-5', 'A-6', 'B-4', 'B-5', 'B-6']
        },
        {
            name: 'Bakery',
            color: '#FF9800',
            positions: ['C-1', 'C-2', 'C-3']
        },
        {
            name: 'Beverages',
            color: '#9C27B0',
            positions: ['C-4', 'C-5', 'C-6', 'D-4', 'D-5', 'D-6']
        },
        {
            name: 'Snacks',
            color: '#F44336',
            positions: ['D-1', 'D-2', 'D-3']
        }
    ]
};

// 목데이터: 실제 매장 상품 위치
const MOCK_LOCATIONS: ProductLocation[] = [
    // Fruits & Vegetables
    { id: '1', position: 'A-1', coordinates: { x: -6, y: 0.5, z: -3.75 }, productName: 'Fresh Apples', category: 'Fruits' },
    { id: '2', position: 'A-2', coordinates: { x: -3.5, y: 0.5, z: -3.75 }, productName: 'Bananas', category: 'Fruits' },
    { id: '3', position: 'A-3', coordinates: { x: -1, y: 0.5, z: -3.75 }, productName: 'Oranges', category: 'Fruits' },
    { id: '4', position: 'B-1', coordinates: { x: -6, y: 0.5, z: -1.25 }, productName: 'Lettuce', category: 'Vegetables' },
    { id: '5', position: 'B-2', coordinates: { x: -3.5, y: 0.5, z: -1.25 }, productName: 'Tomatoes', category: 'Vegetables' },
    { id: '6', position: 'B-3', coordinates: { x: -1, y: 0.5, z: -1.25 }, productName: 'Carrots', category: 'Vegetables' },

    // Dairy & Eggs
    { id: '7', position: 'A-4', coordinates: { x: 1.5, y: 0.5, z: -3.75 }, productName: 'Whole Milk', category: 'Dairy' },
    { id: '8', position: 'A-5', coordinates: { x: 4, y: 0.5, z: -3.75 }, productName: 'Yogurt', category: 'Dairy' },
    { id: '9', position: 'A-6', coordinates: { x: 6.5, y: 0.5, z: -3.75 }, productName: 'Cheese', category: 'Dairy' },
    { id: '10', position: 'B-4', coordinates: { x: 1.5, y: 0.5, z: -1.25 }, productName: 'Eggs', category: 'Dairy' },
    { id: '11', position: 'B-5', coordinates: { x: 4, y: 0.5, z: -1.25 }, productName: 'Butter', category: 'Dairy' },
    { id: '12', position: 'B-6', coordinates: { x: 6.5, y: 0.5, z: -1.25 }, productName: 'Cream', category: 'Dairy' },

    // Bakery
    { id: '13', position: 'C-1', coordinates: { x: -6, y: 0.5, z: 1.25 }, productName: 'Bread', category: 'Bakery' },
    { id: '14', position: 'C-2', coordinates: { x: -3.5, y: 0.5, z: 1.25 }, productName: 'Croissants', category: 'Bakery' },
    { id: '15', position: 'C-3', coordinates: { x: -1, y: 0.5, z: 1.25 }, productName: 'Bagels', category: 'Bakery' },

    // Beverages
    { id: '16', position: 'C-4', coordinates: { x: 1.5, y: 0.5, z: 1.25 }, productName: 'Orange Juice', category: 'Beverages' },
    { id: '17', position: 'C-5', coordinates: { x: 4, y: 0.5, z: 1.25 }, productName: 'Water', category: 'Beverages' },
    { id: '18', position: 'C-6', coordinates: { x: 6.5, y: 0.5, z: 1.25 }, productName: 'Soda', category: 'Beverages' },
    { id: '19', position: 'D-4', coordinates: { x: 1.5, y: 0.5, z: 3.75 }, productName: 'Coffee', category: 'Beverages' },
    { id: '20', position: 'D-5', coordinates: { x: 4, y: 0.5, z: 3.75 }, productName: 'Tea', category: 'Beverages' },
    { id: '21', position: 'D-6', coordinates: { x: 6.5, y: 0.5, z: 3.75 }, productName: 'Energy Drink', category: 'Beverages' },

    // Snacks
    { id: '22', position: 'D-1', coordinates: { x: -6, y: 0.5, z: 3.75 }, productName: 'Chips', category: 'Snacks' },
    { id: '23', position: 'D-2', coordinates: { x: -3.5, y: 0.5, z: 3.75 }, productName: 'Cookies', category: 'Snacks' },
    { id: '24', position: 'D-3', coordinates: { x: -1, y: 0.5, z: 3.75 }, productName: 'Chocolate', category: 'Snacks' },
];

// 선반 컴포넌트
function Shelf({
    position,
    color = '#8B7355'
}: {
    position: [number, number, number];
    color?: string;
}) {
    return (
        <mesh position={position}>
            <boxGeometry args={[2, 2, 0.5]} />
            <meshStandardMaterial color={color} />
        </mesh>
    );
}

// 위치 마커 컴포넌트
function LocationMarker({ location }: { location: ProductLocation }) {
    return (
        <group position={[location.coordinates.x, location.coordinates.y, location.coordinates.z]}>
            {/* 마커 핀 */}
            <mesh position={[0, 0.5, 0]}>
                <coneGeometry args={[0.2, 0.6, 8]} />
                <meshStandardMaterial color="#EA352B" emissive="#EA352B" emissiveIntensity={0.3} />
            </mesh>

            {/* 마커 베이스 */}
            <mesh position={[0, 0.1, 0]}>
                <cylinderGeometry args={[0.25, 0.25, 0.1, 16]} />
                <meshStandardMaterial color="#EA352B" opacity={0.7} transparent />
            </mesh>

            {/* 위치 텍스트 */}
            <Text
                position={[0, 1.3, 0]}
                fontSize={0.25}
                color="white"
                anchorX="center"
                anchorY="middle"
                outlineWidth={0.02}
                outlineColor="#000000"
            >
                {location.position}
            </Text>

            {/* 상품명 텍스트 (작게) */}
            {location.productName && (
                <Text
                    position={[0, 1.0, 0]}
                    fontSize={0.15}
                    color="#CCCCCC"
                    anchorX="center"
                    anchorY="middle"
                >
                    {location.productName}
                </Text>
            )}
        </group>
    );
}

// 사용자(카트) 마커 컴포넌트
function UserMarker({ position }: { position: { x: number; y: number; z: number } }) {
    return (
        <group position={[position.x, position.y, position.z]}>
            {/* 파란색 구체 (사용자 위치) */}
            <mesh position={[0, 0.4, 0]}>
                <sphereGeometry args={[0.35, 16, 16]} />
                <meshStandardMaterial
                    color="#2196F3"
                    emissive="#2196F3"
                    emissiveIntensity={0.5}
                    metalness={0.3}
                    roughness={0.4}
                />
            </mesh>

            {/* 펄스 효과 링 */}
            <mesh position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                <ringGeometry args={[0.4, 0.5, 32]} />
                <meshBasicMaterial color="#2196F3" opacity={0.4} transparent />
            </mesh>

            {/* "YOU" 텍스트 */}
            <Text
                position={[0, 1.2, 0]}
                fontSize={0.35}
                color="white"
                anchorX="center"
                anchorY="middle"
                outlineWidth={0.03}
                outlineColor="#000000"
                fontWeight="bold"
            >
                YOU
            </Text>

            {/* 방향 화살표 (위쪽) */}
            <mesh position={[0, 0.8, 0]} rotation={[0, 0, 0]}>
                <coneGeometry args={[0.15, 0.3, 3]} />
                <meshStandardMaterial color="#2196F3" />
            </mesh>
        </group>
    );
}

// 3D 씬 컴포넌트
function StoreScene({
    locations,
    layout,
    userPosition
}: {
    locations: ProductLocation[];
    layout: StoreLayout;
    userPosition?: { x: number; y: number; z: number };
}) {
    const { gridSize, shelfSpacing, sections } = layout;

    // 선반 위치 계산
    const shelves: Array<{ position: [number, number, number]; color: string }> = [];
    const rows = ['A', 'B', 'C', 'D'];

    for (let row = 0; row < gridSize.rows; row++) {
        for (let col = 0; col < gridSize.cols; col++) {
            const x = (col - gridSize.cols / 2 + 0.5) * shelfSpacing.x;
            const z = (row - gridSize.rows / 2 + 0.5) * shelfSpacing.z;
            const position = `${rows[row]}-${col + 1}`;

            // 섹션 색상 찾기
            let color = '#8B7355'; // 기본 색상
            if (sections) {
                const section = sections.find(s => s.positions.includes(position));
                if (section) {
                    color = section.color;
                }
            }

            shelves.push({ position: [x, 0, z], color });
        }
    }

    return (
        <>
            {/* 조명 */}
            <ambientLight intensity={0.6} />
            <directionalLight position={[10, 15, 5]} intensity={0.8} castShadow />
            <pointLight position={[-10, 10, -5]} intensity={0.4} />
            <hemisphereLight args={['#ffffff', '#444444', 0.3]} />

            {/* 바닥 */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]} receiveShadow>
                <planeGeometry args={[30, 30]} />
                <meshStandardMaterial color="#F5F5F5" />
            </mesh>

            {/* 바닥 그리드 라인 */}
            <gridHelper args={[30, 30, '#CCCCCC', '#E0E0E0']} position={[0, -0.49, 0]} />

            {/* 선반들 */}
            {shelves.map((shelf, index) => (
                <Shelf key={`shelf-${index}`} position={shelf.position} color={shelf.color} />
            ))}

            {/* 위치 마커들 */}
            {locations.map((location) => (
                <LocationMarker key={location.id} location={location} />
            ))}

            {/* 사용자(카트) 위치 */}
            {userPosition && <UserMarker position={userPosition} />}

            {/* 카메라 컨트롤 */}
            <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                minDistance={8}
                maxDistance={30}
                maxPolarAngle={Math.PI / 2.2}
            />

            {/* 카메라 */}
            <PerspectiveCamera makeDefault position={[12, 12, 12]} fov={50} />
        </>
    );
}

/**
 * Three.js 기반 3D 매장 지도 컴포넌트
 * 상품 위치를 3D 환경에서 시각화
 * 
 * @example
 * // 기본 사용 (목데이터)
 * <StoreMap />
 * 
 * @example
 * // 커스텀 레이아웃
 * <StoreMap 
 *   layout={{ gridSize: { rows: 5, cols: 8 }, shelfSpacing: { x: 3, z: 3 } }}
 *   locations={customLocations}
 * />
 */
export default function StoreMap({
    locations = MOCK_LOCATIONS,
    layout = DEFAULT_LAYOUT,
    userPosition = { x: 0, y: 0.5, z: 6 }, // 목데이터: 매장 입구 (남쪽)
    className = ''
}: StoreMapProps) {
    return (
        <div className={`w-full h-full bg-gray-900 rounded-lg overflow-hidden ${className}`}>
            <Canvas shadows>
                <StoreScene locations={locations} layout={layout} userPosition={userPosition} />
            </Canvas>
        </div>
    );
}
