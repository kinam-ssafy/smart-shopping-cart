'use client';

import { useRef, useEffect, useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Text } from '@react-three/drei';
import * as THREE from 'three';

// QGIS에서 추출한 좌표 데이터 (coords.json)
const MAP_DATA = {
    map: [
        [
            [
                [-4.624976595934472, 1.3254630661555717],
                [4.069352933309467, 3.327446839336742],
                [4.21235177425098, 2.9556498528888104],
                [4.584148760698913, 2.9842496210771126],
                [5.327742733594775, -0.19032464782445757],
                [5.985537401925733, -0.2761239523893648],
                [6.357334388373662, -2.363907030135443],
                [7.329726506775945, -2.1923084210056274],
                [8.502317002496344, -4.766287557952847],
                [9.303110511768814, -4.594688948823032],
                [9.61770796184014, -5.452681994472105],
                [9.04571259807409, -5.624280603601919],
                [9.674907498216744, -7.254467390335158],
                [9.074312366262394, -7.454665767653276],
                [9.646307730028443, -8.512857190620466],
                [9.24591097539221, -8.713055567938582],
                [10.647299616619026, -12.288026591476388],
                [4.870146442581936, -13.889613610021325],
                [4.727147601640423, -13.37481778263188],
                [3.8405547878030486, -13.546416391761692],
                [3.7261557150498383, -14.061212219151138],
                [-2.336995140870277, -15.205202946683237],
                [-2.565793286376697, -14.490208741975675],
                [-2.8231912000714185, -14.46160897378737],
                [-2.8231912000714185, -14.833405960235304],
                [-3.252187722895955, -14.862005728423608],
                [-3.5667851729672817, -9.771246990905773],
                [-2.622992822753302, -9.285050931704632],
                [-3.1377886501427454, -7.311666926711764],
                [-2.336995140870277, -7.025669244828739],
                [-2.7373918955065113, -5.16668431258908],
                [-3.766983550285399, -4.508889644258124],
                [-4.939574046005799, 0.18147233862347445],
                [-4.224579841298238, 0.5818690932597081],
                [-4.281779377674843, 0.896466543331035],
                [-4.710775900499379, 0.9822658478959423],
                [-4.682176132311077, 1.3254630661555717],
                [-4.624976595934472, 1.3254630661555717]
            ]
        ]
    ],
    shelves: [
        // Shelf 1
        [[[-2.017344, 0.096393], [-1.153055, -3.252726], [0.53951, -2.892605], [-0.360791, 0.456514], [-2.017344, 0.096393]]],
        // Shelf 2
        [[[1.187727, 0.888658], [2.052015, -2.460461], [3.744581, -2.100341], [2.84428, 1.248778], [1.187727, 0.888658]]],
        // Shelf 3
        [[[-0.792935, -9.626855], [0.071354, -12.975974], [1.763919, -12.615854], [0.863618, -9.266735], [-0.792935, -9.626855]]],
        // Shelf 4
        [[[2.448148, -8.906614], [3.312437, -12.255733], [5.005002, -11.895613], [4.104701, -8.546494], [2.448148, -8.906614]]],
        // Shelf 5
        [[[5.401134, -8.258398], [6.265423, -11.607517], [7.957989, -11.247396], [7.057688, -7.898278], [5.401134, -8.258398]]],
        // Shelf 6
        [[[-1.225079, -4.549159], [-0.360791, -7.898278], [1.331775, -7.538157], [0.431474, -4.189038], [-1.225079, -4.549159]]]
    ]
};

interface UserPosition {
    x: number;
    y: number;
    theta: number;
}

interface ProductLocation {
    id: string;
    position: string; // "A-1", "B-3" 등
    coordinates: { x: number; y: number; z: number };
    productName?: string;
    category?: string;
}

interface StoreMapProps {
    locations?: ProductLocation[];
    className?: string;
}

// 목데이터 업데이트 (새 좌표계에 맞춤)
// 실제 DB 연동시 API에서 받아와야 함. 여기서는 예시로 일부만 수정.
const MOCK_LOCATIONS: ProductLocation[] = [
    // 예시 위치 (대략 선반 1 근처)
    { id: '1', position: 'A-1', coordinates: { x: -0.5, y: 1.0, z: -1.5 }, productName: '사과', category: '과일' },
    // 예시 위치 (대략 선반 6 근처)
    { id: '2', position: 'F-1', coordinates: { x: 0.0, y: 1.0, z: -6.0 }, productName: '냉동만두', category: '냉동' },
];

/**
 * 다각형 데이터를 기반으로 2D Shape 생성
 */
function createShapeFromCoordinates(coords: number[][]) {
    const shape = new THREE.Shape();
    if (coords.length > 0) {
        // Z축(위도/y)을 -Z로 매핑하여 3D 좌표계(x, y, z)와 QGIS(x, y) 매칭
        // Three.js: x=x, z=-y (Top view 기준)
        const startX = coords[0][0];
        const startZ = -coords[0][1];

        shape.moveTo(startX, startZ);

        for (let i = 1; i < coords.length; i++) {
            const x = coords[i][0];
            const z = -coords[i][1];
            shape.lineTo(x, z);
        }
    }
    return shape;
}

/**
 * 매장 바닥/벽면 컴포넌트
 */
function MapBoundary() {
    const shape = useMemo(() => {
        // MultiPolygon의 첫 번째 Polygon의 첫 번째 Ring(외곽선)만 사용
        return createShapeFromCoordinates(MAP_DATA.map[0][0]);
    }, []);

    const extrudeSettings = {
        steps: 1,
        depth: 2.5, // 벽 높이
        bevelEnabled: false,
    };

    return (
        <group>
            {/* 바닥 (ShapeGeometry) */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
                <shapeGeometry args={[shape]} />
                <meshStandardMaterial color="#E0E0E0" side={THREE.DoubleSide} />
            </mesh>

            {/* 벽 (ExtrudeGeometry) - 바닥에서 올라오도록 설정 */}
            {/* ExtrudeGeometry는 기본적으로 Z축으로 돌출됨. 
                 우리는 바닥(XZ평면)에 누워있는 쉐이프를 Y축으로 돌출시켜야 함.
                 따라서 쉐이프를 XY평면에 그리고 회전시킨 뒤 Extrude하거나,
                 Extrude 후 회전시켜야 함.
             */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
                <extrudeGeometry args={[shape, extrudeSettings]} />
                <meshStandardMaterial color="#FAFAFA" transparent opacity={0.3} side={THREE.DoubleSide} />
                {/* 벽만 보이게 하려면 재질을 조정하거나 엣지만 렌더링 할 수도 있음 */}
            </mesh>

            {/* 벽 높이만큼의 와이어프레임 (시각적 구분용) */}
            <lineSegments position={[0, 2.5, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                <edgesGeometry args={[new THREE.ShapeGeometry(shape)]} />
                <lineBasicMaterial color="#9E9E9E" linewidth={2} />
            </lineSegments>
            <lineSegments position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                <edgesGeometry args={[new THREE.ShapeGeometry(shape)]} />
                <lineBasicMaterial color="#424242" linewidth={2} />
            </lineSegments>
        </group>
    );
}

// 선반 메타데이터 (DB 카테고리 매핑 및 스타일)
const SHELF_INFO = [
    { id: 'A', name: '청과/과일', type: 'standard', color: '#8BC34A', products: ['사과', '바나나', '포도'] },     // Index 0
    { id: 'B', name: '채소/버섯', type: 'standard', color: '#4CAF50', products: ['시금치', '당근', '버섯'] },     // Index 1
    { id: 'C', name: '정육/유제품', type: 'refrigerator', color: '#2196F3', products: ['우유', '치즈', '소고기'] }, // Index 2
    { id: 'D', name: '수산/음료', type: 'refrigerator', color: '#03A9F4', products: ['생선', '생수', '주스'] },   // Index 3
    { id: 'E', name: '과자/커피', type: 'standard', color: '#795548', products: ['과자', '초콜릿', '커피'] },     // Index 4
    { id: 'F', name: '냉동/생활', type: 'freezer', color: '#673AB7', products: ['만두', '아이스크림', '휴지'] }    // Index 5
];

/**
 * 다각형 선반 컴포넌트 (스타일 적용)
 */
function PolygonShelf({ coords, index }: { coords: number[][]; index: number }) {
    const shape = useMemo(() => {
        return createShapeFromCoordinates(coords);
    }, [coords]);

    const info = SHELF_INFO[index % SHELF_INFO.length];

    // 중심점 계산 (라벨/아이콘 표시용)
    const center = useMemo(() => {
        let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
        coords.forEach(p => {
            const x = p[0];
            const z = p[1]; // Fix: Use p[1] directly for Z because Mesh Z = -ShapeY = -(-p[1]) = p[1]
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (z < minZ) minZ = z;
            if (z > maxZ) maxZ = z;
        });
        return [(minX + maxX) / 2, (minZ + maxZ) / 2];
    }, [coords]);

    // === 스타일별 렌더링 ===

    // 1. 냉동고 (Freezer) - 낮은 평대형
    if (info.type === 'freezer') {
        const bodySettings = { steps: 1, depth: 1.0, bevelEnabled: false }; // 높이 1.0
        return (
            <group>
                {/* 본체 */}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} castShadow receiveShadow>
                    <extrudeGeometry args={[shape, bodySettings]} />
                    <meshStandardMaterial color="#E1F5FE" />
                </mesh>
                {/* 상단 유리 커버 느낌 */}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 1.01, 0]}>
                    <shapeGeometry args={[shape]} />
                    <meshStandardMaterial color="#81D4FA" transparent opacity={0.5} side={THREE.DoubleSide} />
                </mesh>
                {/* 라벨 */}
                <ShelfLabel center={center} label={info.name} subLabel={`Bay ${info.id}`} height={1.8} color="#5E35B1" />
            </group>
        );
    }

    // 2. 냉장고 (Refrigerator) - 수직형 오픈 쇼케이스 느낌
    if (info.type === 'refrigerator') {
        const bodySettings = { steps: 1, depth: 2.2, bevelEnabled: false };
        return (
            <group>
                {/* 본체 (약간 투명한 느낌의 쿨러) */}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} castShadow>
                    <extrudeGeometry args={[shape, bodySettings]} />
                    <meshStandardMaterial color="#E3F2FD" transparent opacity={0.8} />
                </mesh>
                {/* 내부 선반들 (가로선 느낌) */}
                {[0.5, 1.0, 1.5].map((y, i) => (
                    <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, y, 0]}>
                        {/* 약간 작게? 복잡하니 그냥 같은 쉐이프 사용 */}
                        <shapeGeometry args={[shape]} />
                        <meshStandardMaterial color="#90CAF9" />
                    </mesh>
                ))}
                {/* 상단 헤더 */}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 2.2, 0]}>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.2, bevelEnabled: false }]} />
                    <meshStandardMaterial color={info.color} />
                </mesh>
                <ShelfLabel center={center} label={info.name} subLabel={`Bay ${info.id}`} height={2.8} color={info.color} />
            </group>
        );
    }

    // 3. 일반 선반 (Standard) - 3단 오픈형
    const tierHeight = 0.1;
    const tiers = [0.4, 1.1, 1.8]; // 선반 높이들
    return (
        <group>
            {/* 기둥 (쉐이프의 꼭짓점에 기둥 세우기는 복잡하므로, 전체 쉐이프를 투명한 박스처럼 감싸거나 생략) */}

            {/* 각 층의 선반판 */}
            {tiers.map((y, i) => (
                <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, y, 0]} castShadow receiveShadow>
                    <extrudeGeometry args={[shape, { steps: 1, depth: tierHeight, bevelEnabled: false }]} />
                    <meshStandardMaterial color="#D7CCC8" /> // 나무 색상
                </mesh>
            ))}

            {/* 상품들 (각 층에 박스 형태로 대충 표현) */}
            {tiers.map((y, i) => (
                <mesh key={`prod-${i}`} rotation={[-Math.PI / 2, 0, 0]} position={[0, y + tierHeight, 0]}>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.3, bevelEnabled: false }]} />
                    {/* scale을 조금 줄여서 선반 안쪽에 있는 것처럼 보이게 하면 좋겠지만 복잡함. */}
                    <meshStandardMaterial color={info.color} />
                </mesh>
            ))}

            <ShelfLabel center={center} label={info.name} subLabel={`Bay ${info.id}`} height={2.5} color="#5D4037" />
        </group>
    );
}

function ShelfLabel({ center, label, subLabel, height, color }: any) {
    return (
        <group position={[center[0], height, center[1]]}>
            <Text
                fontSize={0.4}
                color="white"
                anchorX="center"
                anchorY="bottom"
                outlineWidth={0.04}
                outlineColor="#000"
            >
                {label}
            </Text>
            <Text
                position={[0, -0.45, 0]}
                fontSize={0.25}
                color={color}
                anchorX="center"
                anchorY="bottom"
                outlineWidth={0.02}
                outlineColor="#FFF"
            >
                {subLabel}
            </Text>
        </group>
    );
}

// 사용자(카트) 마커
function UserMarker({ position }: { position: UserPosition }) {
    // 좌표 변환: 입력받은 2D (x, y) -> Three.js 3D (x, 0, -y)
    // 회전 변환: theta (도) -> 라디안. 
    // QGIS/수학적 각도(반시계)를 Three.js(반시계)로 적용. 
    // 단, Z축이 반전(-y)되었으므로 회전 방향도 고려 필요할 수 있음. 우선 그대로 적용.
    const threeX = position.x;
    const threeZ = -position.y;
    const rotationRad = -position.theta * (Math.PI / 180); // 시계 방향 회전 보정 (필요시 조정)

    return (
        <group position={[threeX, 0, threeZ]} rotation={[0, rotationRad, 0]}>
            <mesh position={[0, 0.4, 0]}>
                <sphereGeometry args={[0.3, 16, 16]} />
                <meshStandardMaterial color="#F44336" emissive="#EF9A9A" emissiveIntensity={0.5} />
            </mesh>
            {/* 화살표로 방향 표시 */}
            <mesh position={[0, 0.4, -0.4]} rotation={[-Math.PI / 2, 0, 0]}>
                <coneGeometry args={[0.15, 0.3, 8]} />
                <meshStandardMaterial color="#F44336" />
            </mesh>
            <Text
                position={[0, 0.9, 0]}
                fontSize={0.3}
                color="white"
                outlineWidth={0.03}
                outlineColor="#000"
                anchorX="center"
            // 텍스트는 항상 정면을 보게 하려면 billboard 효과 필요하지만 일단 회전 따라가게 둠
            >
                YOU
            </Text>
        </group>
    );
}

function StoreScene({ locations, userPosition }: { locations: ProductLocation[]; userPosition: UserPosition }) {
    return (
        <>
            <ambientLight intensity={0.6} />
            <directionalLight position={[10, 20, 5]} intensity={0.8} castShadow />
            <hemisphereLight args={['#ffffff', '#444444', 0.4]} />

            <MapBoundary />

            {MAP_DATA.shelves.map((shelfPoly, idx) => (
                <PolygonShelf key={idx} coords={shelfPoly[0]} index={idx} />
            ))}

            <UserMarker position={userPosition} />

            <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                target={[2, 0, -7]}
            />
            <PerspectiveCamera makeDefault position={[5, 15, 10]} fov={50} />

            <gridHelper args={[50, 50, '#EEEEEE', '#EEEEEE']} position={[0, -0.1, 0]} />
        </>
    );
}

export default function StoreMap({
    locations = MOCK_LOCATIONS,
    className = ''
}: StoreMapProps) {
    // 현위치 목데이터 (x, y, theta) - 초기값
    const [pos, setPos] = useState<UserPosition>({ x: 0.06, y: 0.11, theta: 18.5 });

    // 실시간 위치 이동 시뮬레이션
    useEffect(() => {
        const interval = setInterval(() => {
            setPos((prev: UserPosition) => {
                // 간단한 원형 이동 시뮬레이션
                const time = Date.now() / 1000;
                const radius = 3;
                const centerX = 0;
                const centerY = 3; // 맵 상에서의 Y (Three.js Z로는 -3)

                // 실제 입력 데이터 예시와 유사하게 생성
                const newX = centerX + Math.cos(time) * radius;
                const newY = centerY + Math.sin(time) * radius;

                // 진행 방향 (접선)
                const newTheta = (Math.atan2(Math.cos(time), -Math.sin(time)) * 180 / Math.PI);

                return {
                    x: Number(newX.toFixed(2)),
                    y: Number(newY.toFixed(2)),
                    theta: Number(newTheta.toFixed(1))
                };
            });
        }, 100);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className={`w-full h-full bg-gray-900 rounded-lg overflow-hidden ${className}`}>
            {/* 디버그 패널 */}
            <div className="absolute top-4 left-4 z-10 bg-black/50 text-white p-2 rounded text-xs">
                <p>User Position JSON:</p>
                <pre>{JSON.stringify(pos, null, 2)}</pre>
            </div>

            <Canvas shadows>
                <StoreScene locations={locations} userPosition={pos} />
            </Canvas>
        </div>
    );
}
