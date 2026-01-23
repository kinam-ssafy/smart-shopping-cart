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

// 기본 레이아웃 설정 (실제 마트 형태)
const DEFAULT_LAYOUT: StoreLayout = {
    gridSize: { rows: 6, cols: 8 },
    shelfSpacing: { x: 2.8, z: 2.8 },
    sections: [
        // 신선식품 구역 (입구 근처)
        {
            name: '🥬 청과/채소',
            color: '#2E7D32',
            positions: ['A-1', 'A-2', 'A-3', 'B-1', 'B-2', 'B-3']
        },
        {
            name: '🍎 과일',
            color: '#66BB6A',
            positions: ['A-4', 'A-5', 'B-4', 'B-5']
        },
        // 정육/수산 (냉장 구역)
        {
            name: '🥩 정육',
            color: '#C62828',
            positions: ['A-6', 'A-7', 'A-8', 'B-6', 'B-7', 'B-8']
        },
        {
            name: '🐟 수산',
            color: '#1565C0',
            positions: ['C-6', 'C-7', 'C-8', 'D-6', 'D-7', 'D-8']
        },
        // 유제품/냉동
        {
            name: '🧈 유제품',
            color: '#42A5F5',
            positions: ['C-1', 'C-2', 'C-3', 'D-1', 'D-2', 'D-3']
        },
        {
            name: '🧊 냉동식품',
            color: '#7E57C2',
            positions: ['C-4', 'C-5', 'D-4', 'D-5']
        },
        // 가공식품/조미료
        {
            name: '🍜 라면/면류',
            color: '#FF7043',
            positions: ['E-1', 'E-2', 'E-3']
        },
        {
            name: '🧂 조미료/소스',
            color: '#8D6E63',
            positions: ['E-4', 'E-5', 'E-6']
        },
        // 음료/과자
        {
            name: '🥤 음료',
            color: '#26A69A',
            positions: ['F-1', 'F-2', 'F-3', 'F-4']
        },
        {
            name: '🍪 과자/스낵',
            color: '#FFA726',
            positions: ['F-5', 'F-6', 'F-7', 'F-8']
        },
        // 생활용품
        {
            name: '🧴 생활용품',
            color: '#78909C',
            positions: ['E-7', 'E-8']
        }
    ]
};

// 목데이터: 실제 매장 상품 위치 (한국 마트 스타일)
const MOCK_LOCATIONS: ProductLocation[] = [
    // 🥬 청과/채소
    { id: '1', position: 'A-1', coordinates: { x: -9.8, y: 0.5, z: -7 }, productName: '배추', category: '채소' },
    { id: '2', position: 'A-2', coordinates: { x: -7, y: 0.5, z: -7 }, productName: '시금치', category: '채소' },
    { id: '3', position: 'A-3', coordinates: { x: -4.2, y: 0.5, z: -7 }, productName: '양파/마늘', category: '채소' },
    { id: '4', position: 'B-1', coordinates: { x: -9.8, y: 0.5, z: -4.2 }, productName: '감자/고구마', category: '채소' },
    { id: '5', position: 'B-2', coordinates: { x: -7, y: 0.5, z: -4.2 }, productName: '당근/무', category: '채소' },
    { id: '6', position: 'B-3', coordinates: { x: -4.2, y: 0.5, z: -4.2 }, productName: '파프리카', category: '채소' },

    // 🍎 과일
    { id: '7', position: 'A-4', coordinates: { x: -1.4, y: 0.5, z: -7 }, productName: '사과', category: '과일' },
    { id: '8', position: 'A-5', coordinates: { x: 1.4, y: 0.5, z: -7 }, productName: '바나나', category: '과일' },
    { id: '9', position: 'B-4', coordinates: { x: -1.4, y: 0.5, z: -4.2 }, productName: '오렌지/귤', category: '과일' },
    { id: '10', position: 'B-5', coordinates: { x: 1.4, y: 0.5, z: -4.2 }, productName: '딸기/포도', category: '과일' },

    // 🥩 정육
    { id: '11', position: 'A-6', coordinates: { x: 4.2, y: 0.5, z: -7 }, productName: '소고기', category: '정육' },
    { id: '12', position: 'A-7', coordinates: { x: 7, y: 0.5, z: -7 }, productName: '돼지고기', category: '정육' },
    { id: '13', position: 'A-8', coordinates: { x: 9.8, y: 0.5, z: -7 }, productName: '닭고기', category: '정육' },
    { id: '14', position: 'B-6', coordinates: { x: 4.2, y: 0.5, z: -4.2 }, productName: '양념육', category: '정육' },
    { id: '15', position: 'B-7', coordinates: { x: 7, y: 0.5, z: -4.2 }, productName: '햄/소시지', category: '정육' },
    { id: '16', position: 'B-8', coordinates: { x: 9.8, y: 0.5, z: -4.2 }, productName: '베이컨', category: '정육' },

    // 🐟 수산
    { id: '17', position: 'C-6', coordinates: { x: 4.2, y: 0.5, z: -1.4 }, productName: '생선류', category: '수산' },
    { id: '18', position: 'C-7', coordinates: { x: 7, y: 0.5, z: -1.4 }, productName: '새우/조개', category: '수산' },
    { id: '19', position: 'C-8', coordinates: { x: 9.8, y: 0.5, z: -1.4 }, productName: '오징어/문어', category: '수산' },
    { id: '20', position: 'D-6', coordinates: { x: 4.2, y: 0.5, z: 1.4 }, productName: '회/초밥', category: '수산' },
    { id: '21', position: 'D-7', coordinates: { x: 7, y: 0.5, z: 1.4 }, productName: '훈제연어', category: '수산' },
    { id: '22', position: 'D-8', coordinates: { x: 9.8, y: 0.5, z: 1.4 }, productName: '게/랍스터', category: '수산' },

    // 🧈 유제품
    { id: '23', position: 'C-1', coordinates: { x: -9.8, y: 0.5, z: -1.4 }, productName: '우유', category: '유제품' },
    { id: '24', position: 'C-2', coordinates: { x: -7, y: 0.5, z: -1.4 }, productName: '요거트', category: '유제품' },
    { id: '25', position: 'C-3', coordinates: { x: -4.2, y: 0.5, z: -1.4 }, productName: '치즈', category: '유제품' },
    { id: '26', position: 'D-1', coordinates: { x: -9.8, y: 0.5, z: 1.4 }, productName: '버터/마가린', category: '유제품' },
    { id: '27', position: 'D-2', coordinates: { x: -7, y: 0.5, z: 1.4 }, productName: '계란', category: '유제품' },
    { id: '28', position: 'D-3', coordinates: { x: -4.2, y: 0.5, z: 1.4 }, productName: '두부/콩나물', category: '유제품' },

    // 🧊 냉동식품
    { id: '29', position: 'C-4', coordinates: { x: -1.4, y: 0.5, z: -1.4 }, productName: '냉동만두', category: '냉동' },
    { id: '30', position: 'C-5', coordinates: { x: 1.4, y: 0.5, z: -1.4 }, productName: '냉동피자', category: '냉동' },
    { id: '31', position: 'D-4', coordinates: { x: -1.4, y: 0.5, z: 1.4 }, productName: '아이스크림', category: '냉동' },
    { id: '32', position: 'D-5', coordinates: { x: 1.4, y: 0.5, z: 1.4 }, productName: '냉동밥', category: '냉동' },

    // 🍜 라면/면류
    { id: '33', position: 'E-1', coordinates: { x: -9.8, y: 0.5, z: 4.2 }, productName: '라면', category: '면류' },
    { id: '34', position: 'E-2', coordinates: { x: -7, y: 0.5, z: 4.2 }, productName: '우동/소바', category: '면류' },
    { id: '35', position: 'E-3', coordinates: { x: -4.2, y: 0.5, z: 4.2 }, productName: '스파게티', category: '면류' },

    // 🧂 조미료/소스
    { id: '36', position: 'E-4', coordinates: { x: -1.4, y: 0.5, z: 4.2 }, productName: '간장/된장', category: '조미료' },
    { id: '37', position: 'E-5', coordinates: { x: 1.4, y: 0.5, z: 4.2 }, productName: '고추장/쌈장', category: '조미료' },
    { id: '38', position: 'E-6', coordinates: { x: 4.2, y: 0.5, z: 4.2 }, productName: '식용유/참기름', category: '조미료' },

    // 🧴 생활용품
    { id: '39', position: 'E-7', coordinates: { x: 7, y: 0.5, z: 4.2 }, productName: '세제/섬유유연제', category: '생활' },
    { id: '40', position: 'E-8', coordinates: { x: 9.8, y: 0.5, z: 4.2 }, productName: '화장지/물티슈', category: '생활' },

    // 🥤 음료
    { id: '41', position: 'F-1', coordinates: { x: -9.8, y: 0.5, z: 7 }, productName: '생수', category: '음료' },
    { id: '42', position: 'F-2', coordinates: { x: -7, y: 0.5, z: 7 }, productName: '탄산음료', category: '음료' },
    { id: '43', position: 'F-3', coordinates: { x: -4.2, y: 0.5, z: 7 }, productName: '주스', category: '음료' },
    { id: '44', position: 'F-4', coordinates: { x: -1.4, y: 0.5, z: 7 }, productName: '커피/차', category: '음료' },

    // 🍪 과자/스낵
    { id: '45', position: 'F-5', coordinates: { x: 1.4, y: 0.5, z: 7 }, productName: '과자', category: '스낵' },
    { id: '46', position: 'F-6', coordinates: { x: 4.2, y: 0.5, z: 7 }, productName: '초콜릿/사탕', category: '스낵' },
    { id: '47', position: 'F-7', coordinates: { x: 7, y: 0.5, z: 7 }, productName: '견과류', category: '스낵' },
    { id: '48', position: 'F-8', coordinates: { x: 9.8, y: 0.5, z: 7 }, productName: '젤리/껌', category: '스낵' },
];

// 선반 타입 정의
type ShelfType = 'normal' | 'refrigerator' | 'freezer' | 'end-cap';

// 일반 선반 컴포넌트 (3단 선반)
function Shelf({
    position,
    color = '#8B7355',
    shelfType = 'normal',
    rotation = 0
}: {
    position: [number, number, number];
    color?: string;
    shelfType?: ShelfType;
    rotation?: number;
}) {
    if (shelfType === 'refrigerator') {
        return (
            <group position={position} rotation={[0, rotation, 0]}>
                {/* 냉장고 본체 */}
                <mesh position={[0, 1, 0]}>
                    <boxGeometry args={[2.2, 2.5, 0.8]} />
                    <meshStandardMaterial color="#E3F2FD" metalness={0.3} roughness={0.4} />
                </mesh>
                {/* 냉장고 유리문 */}
                <mesh position={[0, 1, 0.35]}>
                    <boxGeometry args={[2, 2.3, 0.05]} />
                    <meshStandardMaterial color="#90CAF9" opacity={0.6} transparent metalness={0.5} />
                </mesh>
                {/* 냉장고 손잡이 */}
                <mesh position={[0.85, 1, 0.4]}>
                    <boxGeometry args={[0.05, 0.8, 0.05]} />
                    <meshStandardMaterial color="#BDBDBD" metalness={0.8} />
                </mesh>
                {/* 상단 조명 */}
                <mesh position={[0, 2.35, 0.2]}>
                    <boxGeometry args={[1.8, 0.08, 0.3]} />
                    <meshStandardMaterial color="#BBDEFB" emissive="#64B5F6" emissiveIntensity={0.3} />
                </mesh>
            </group>
        );
    }

    if (shelfType === 'freezer') {
        return (
            <group position={position} rotation={[0, rotation, 0]}>
                {/* 냉동고 본체 */}
                <mesh position={[0, 0.6, 0]}>
                    <boxGeometry args={[2.2, 1.2, 1]} />
                    <meshStandardMaterial color="#E1F5FE" metalness={0.2} roughness={0.5} />
                </mesh>
                {/* 냉동고 유리 뚜껑 */}
                <mesh position={[0, 1.15, 0]}>
                    <boxGeometry args={[2, 0.1, 0.9]} />
                    <meshStandardMaterial color="#B3E5FC" opacity={0.5} transparent />
                </mesh>
                {/* 냉동고 테두리 */}
                <mesh position={[0, 1.2, 0]}>
                    <boxGeometry args={[2.2, 0.05, 1]} />
                    <meshStandardMaterial color="#0288D1" />
                </mesh>
            </group>
        );
    }

    // 일반 3단 선반
    return (
        <group position={position} rotation={[0, rotation, 0]}>
            {/* 선반 프레임 (측면) */}
            <mesh position={[-0.95, 1, 0]}>
                <boxGeometry args={[0.08, 2.2, 0.6]} />
                <meshStandardMaterial color="#5D4037" />
            </mesh>
            <mesh position={[0.95, 1, 0]}>
                <boxGeometry args={[0.08, 2.2, 0.6]} />
                <meshStandardMaterial color="#5D4037" />
            </mesh>

            {/* 3단 선반판 */}
            {[0.3, 1.0, 1.7].map((y, i) => (
                <mesh key={i} position={[0, y, 0]}>
                    <boxGeometry args={[1.9, 0.08, 0.55]} />
                    <meshStandardMaterial color={color} />
                </mesh>
            ))}

            {/* 상품 모형 (각 선반에) */}
            {[0.5, 1.2, 1.9].map((y, i) => (
                <group key={`products-${i}`}>
                    <mesh position={[-0.5, y, 0]}>
                        <boxGeometry args={[0.3, 0.35, 0.25]} />
                        <meshStandardMaterial color={color} opacity={0.8} transparent />
                    </mesh>
                    <mesh position={[0, y, 0]}>
                        <boxGeometry args={[0.3, 0.35, 0.25]} />
                        <meshStandardMaterial color={color} opacity={0.8} transparent />
                    </mesh>
                    <mesh position={[0.5, y, 0]}>
                        <boxGeometry args={[0.3, 0.35, 0.25]} />
                        <meshStandardMaterial color={color} opacity={0.8} transparent />
                    </mesh>
                </group>
            ))}
        </group>
    );
}

// 입구/출구 컴포넌트
function Entrance({ position, label }: { position: [number, number, number]; label: string }) {
    return (
        <group position={position}>
            {/* 자동문 프레임 */}
            <mesh position={[0, 1.5, 0]}>
                <boxGeometry args={[4, 3, 0.2]} />
                <meshStandardMaterial color="#37474F" />
            </mesh>
            {/* 유리문 (좌) */}
            <mesh position={[-1, 1.3, 0.15]}>
                <boxGeometry args={[1.8, 2.4, 0.05]} />
                <meshStandardMaterial color="#81D4FA" opacity={0.4} transparent />
            </mesh>
            {/* 유리문 (우) */}
            <mesh position={[1, 1.3, 0.15]}>
                <boxGeometry args={[1.8, 2.4, 0.05]} />
                <meshStandardMaterial color="#81D4FA" opacity={0.4} transparent />
            </mesh>
            {/* 상단 간판 */}
            <mesh position={[0, 3.2, 0]}>
                <boxGeometry args={[4.5, 0.6, 0.3]} />
                <meshStandardMaterial color="#1976D2" />
            </mesh>
            {/* 입구 텍스트 */}
            <Text
                position={[0, 3.2, 0.2]}
                fontSize={0.35}
                color="white"
                anchorX="center"
                anchorY="middle"
                fontWeight="bold"
            >
                {label}
            </Text>
        </group>
    );
}

// 계산대 컴포넌트
function Checkout({ position, number }: { position: [number, number, number]; number: number }) {
    return (
        <group position={position}>
            {/* 계산대 본체 */}
            <mesh position={[0, 0.5, 0]}>
                <boxGeometry args={[1.5, 1, 2.5]} />
                <meshStandardMaterial color="#455A64" />
            </mesh>
            {/* 컨베이어 벨트 */}
            <mesh position={[0, 1.05, 0.3]}>
                <boxGeometry args={[1.3, 0.1, 1.8]} />
                <meshStandardMaterial color="#212121" />
            </mesh>
            {/* 모니터 */}
            <mesh position={[0, 1.5, -1]}>
                <boxGeometry args={[0.6, 0.5, 0.08]} />
                <meshStandardMaterial color="#263238" />
            </mesh>
            <mesh position={[0, 1.5, -0.95]}>
                <boxGeometry args={[0.5, 0.4, 0.02]} />
                <meshStandardMaterial color="#4FC3F7" emissive="#29B6F6" emissiveIntensity={0.3} />
            </mesh>
            {/* 계산대 번호 */}
            <Text
                position={[0, 1.3, 1.3]}
                fontSize={0.3}
                color="white"
                anchorX="center"
                anchorY="middle"
                outlineWidth={0.02}
                outlineColor="#000"
            >
                {`${number}번`}
            </Text>
        </group>
    );
}

// 기둥 컴포넌트
function Pillar({ position }: { position: [number, number, number] }) {
    return (
        <mesh position={position}>
            <cylinderGeometry args={[0.25, 0.25, 4, 16]} />
            <meshStandardMaterial color="#ECEFF1" metalness={0.1} roughness={0.8} />
        </mesh>
    );
}

// 천장 조명 컴포넌트
function CeilingLight({ position }: { position: [number, number, number] }) {
    return (
        <group position={position}>
            <mesh>
                <boxGeometry args={[2, 0.1, 0.5]} />
                <meshStandardMaterial
                    color="#FFFFFF"
                    emissive="#FFF9C4"
                    emissiveIntensity={0.8}
                />
            </mesh>
            <pointLight position={[0, -0.2, 0]} intensity={0.3} distance={8} color="#FFF9C4" />
        </group>
    );
}

// 벽면 컴포넌트
function Wall({
    position,
    size,
    rotation = 0
}: {
    position: [number, number, number];
    size: [number, number, number];
    rotation?: number;
}) {
    return (
        <mesh position={position} rotation={[0, rotation, 0]}>
            <boxGeometry args={size} />
            <meshStandardMaterial color="#FAFAFA" />
        </mesh>
    );
}

// 카트 보관소 컴포넌트
function CartStorage({ position }: { position: [number, number, number] }) {
    return (
        <group position={position}>
            {/* 카트 여러 대 */}
            {[0, 0.5, 1, 1.5].map((offset, i) => (
                <group key={i} position={[offset, 0, 0]}>
                    {/* 카트 바구니 */}
                    <mesh position={[0, 0.6, 0]}>
                        <boxGeometry args={[0.4, 0.35, 0.6]} />
                        <meshStandardMaterial color="#90A4AE" wireframe />
                    </mesh>
                    {/* 카트 손잡이 */}
                    <mesh position={[0, 1, -0.25]}>
                        <boxGeometry args={[0.35, 0.05, 0.05]} />
                        <meshStandardMaterial color="#546E7A" />
                    </mesh>
                </group>
            ))}
        </group>
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

    // 냉장/냉동 섹션 이름 목록
    const refrigeratorSections = ['🧈 유제품', '🥩 정육', '🐟 수산'];
    const freezerSections = ['🧊 냉동식품'];

    // 선반 위치 및 타입 계산
    const shelves: Array<{
        position: [number, number, number];
        color: string;
        shelfType: ShelfType;
        rotation: number;
    }> = [];
    const rows = ['A', 'B', 'C', 'D', 'E', 'F'];

    for (let row = 0; row < gridSize.rows; row++) {
        for (let col = 0; col < gridSize.cols; col++) {
            const x = (col - gridSize.cols / 2 + 0.5) * shelfSpacing.x;
            const z = (row - gridSize.rows / 2 + 0.5) * shelfSpacing.z;
            const position = `${rows[row]}-${col + 1}`;

            // 섹션 찾기
            let color = '#8B7355';
            let shelfType: ShelfType = 'normal';
            let rotation = 0;

            if (sections) {
                const section = sections.find(s => s.positions.includes(position));
                if (section) {
                    color = section.color;

                    // 섹션별 선반 타입 결정
                    if (refrigeratorSections.includes(section.name)) {
                        shelfType = 'refrigerator';
                    } else if (freezerSections.includes(section.name)) {
                        shelfType = 'freezer';
                    }
                }
            }

            // 선반 방향 (짝수 행은 180도 회전)
            rotation = row % 2 === 0 ? 0 : Math.PI;

            shelves.push({ position: [x, 0, z], color, shelfType, rotation });
        }
    }

    return (
        <>
            {/* 조명 */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 20, 5]} intensity={0.7} castShadow />
            <directionalLight position={[-10, 20, -5]} intensity={0.4} />
            <hemisphereLight args={['#ffffff', '#444444', 0.3]} />

            {/* 바닥 (더 마트 느낌의 타일) */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]} receiveShadow>
                <planeGeometry args={[50, 50]} />
                <meshStandardMaterial color="#E8E8E8" />
            </mesh>

            {/* 통로 표시 (중앙 통로) */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.48, 0]}>
                <planeGeometry args={[3, 50]} />
                <meshStandardMaterial color="#FFF8E1" />
            </mesh>

            {/* 바닥 그리드 라인 */}
            <gridHelper args={[50, 50, '#BDBDBD', '#E0E0E0']} position={[0, -0.47, 0]} />

            {/* ========== 벽면 ========== */}
            {/* 뒷벽 (북쪽) */}
            <Wall position={[0, 2, -14]} size={[50, 5, 0.3]} />
            {/* 좌측 벽 */}
            <Wall position={[-16, 2, 0]} size={[0.3, 5, 30]} />
            {/* 우측 벽 */}
            <Wall position={[16, 2, 0]} size={[0.3, 5, 30]} />

            {/* ========== 입구/출구 ========== */}
            <Entrance position={[-6, 0, 14]} label="입구 ENTRANCE" />
            <Entrance position={[6, 0, 14]} label="출구 EXIT" />

            {/* ========== 계산대 (출구 앞) ========== */}
            {[1, 2, 3, 4].map((num, i) => (
                <Checkout
                    key={`checkout-${num}`}
                    position={[3 + i * 2.5, 0, 11.5]}
                    number={num}
                />
            ))}

            {/* ========== 카트 보관소 (입구 옆) ========== */}
            <CartStorage position={[-11, 0, 12]} />
            <CartStorage position={[-11, 0, 13.5]} />

            {/* ========== 기둥 ========== */}
            {[-12, -4, 4, 12].map((x) => (
                [-10, 0, 10].map((z, i) => (
                    <Pillar key={`pillar-${x}-${z}`} position={[x, 1.5, z]} />
                ))
            ))}

            {/* ========== 천장 조명 ========== */}
            {[-10, -5, 0, 5, 10].map((x) => (
                [-8, -2, 4, 10].map((z) => (
                    <CeilingLight key={`light-${x}-${z}`} position={[x, 4, z]} />
                ))
            ))}

            {/* ========== 선반들 ========== */}
            {shelves.map((shelf, index) => (
                <Shelf
                    key={`shelf-${index}`}
                    position={shelf.position}
                    color={shelf.color}
                    shelfType={shelf.shelfType}
                    rotation={shelf.rotation}
                />
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
                minDistance={10}
                maxDistance={40}
                maxPolarAngle={Math.PI / 2.1}
            />

            {/* 카메라 */}
            <PerspectiveCamera makeDefault position={[18, 18, 25]} fov={50} />
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
