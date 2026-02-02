'use client';

import React, { useEffect, useMemo, useState, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import { OrbitControls as OrbitControlsImpl } from 'three-stdlib';

// ============================================================
// 경로 표시 컴포넌트
// ============================================================
function NavigationPath({ path }: { path: number[][] | null }) {
    const points = useMemo(() => {
        if (!path || path.length < 2) return [];

        // 디버그 로그: 원본 경로 좌표
        console.log('[NavigationPath] 원본 경로:', path);

        // Three.js 좌표 변환: (x, y) → (x, height, -y)
        // Y축을 Z축으로 변환하고 방향 반전
        const converted = path.map((p, i) => {
            const vec = new THREE.Vector3(p[0], 0.15, -p[1]);
            console.log(`[NavigationPath] Point ${i}: (${p[0].toFixed(2)}, ${p[1].toFixed(2)}) → Three.js (${vec.x.toFixed(2)}, ${vec.y.toFixed(2)}, ${vec.z.toFixed(2)})`);
            return vec;
        });

        return converted;
    }, [path]);

    if (points.length < 2) return null;

    // 디버그: 마지막 점(목표 지점) 강조 표시
    const endPoint = points[points.length - 1];
    console.log('[NavigationPath] 목표 지점 (Three.js):', endPoint);

    return (
        <group>
            {/* 메인 경로 라인 (drei Line 컴포넌트 사용) */}
            <Line
                points={points}
                color="#FF5722"
                lineWidth={4}
            />
            {/* 웨이포인트 마커 */}
            {points.map((point, i) => (
                <mesh key={i} position={point}>
                    <sphereGeometry args={[0.2, 16, 16]} />
                    <meshStandardMaterial
                        color={i === 0 ? '#4CAF50' : i === points.length - 1 ? '#F44336' : '#FFC107'}
                        emissive={i === points.length - 1 ? '#F44336' : '#000'}
                        emissiveIntensity={0.5}
                    />
                </mesh>
            ))}
            {/* 디버그: 목표 지점에 큰 원기둥 표시 */}
            <mesh position={[endPoint.x, 1, endPoint.z]}>
                <cylinderGeometry args={[0.3, 0.3, 2, 16]} />
                <meshStandardMaterial color="#F44336" transparent opacity={0.6} />
            </mesh>
        </group>
    );
}

// ============================================================
// API 응답 타입 정의
// ============================================================
interface MapDataResponse {
    storeMap: {
        id: string;
        version: string;
        boundary: number[][];
        units: string;
    };
    fixtures: FixtureData[];
}

interface FixtureData {
    id: string;
    label: string;
    parentCategoryId: string;
    categoryName: string;
    geometry: number[][];
}

interface UserPosition {
    x: number;
    y: number;
    theta: number;
}

interface StoreMapProps {
    className?: string;
    /** 내비게이션 경로 [[x, y], ...] */
    navigationPath?: number[][] | null;
}

// 선반 타입 매핑 (parentCategoryId → 스타일)
const SHELF_STYLES: Record<string, { type: string; color: string }> = {
    'pc-fruits': { type: 'standard', color: '#8BC34A' },
    'pc-vegetables': { type: 'standard', color: '#4CAF50' },
    'pc-meat': { type: 'refrigerator', color: '#2196F3' },
    'pc-dairy': { type: 'refrigerator', color: '#2196F3' },
    'pc-seafood': { type: 'refrigerator', color: '#03A9F4' },
    'pc-beverages': { type: 'refrigerator', color: '#03A9F4' },
    'pc-snacks': { type: 'standard', color: '#795548' },
    'pc-frozen': { type: 'freezer', color: '#673AB7' },
    'pc-household': { type: 'standard', color: '#9E9E9E' },
};

// ============================================================
// 유틸리티 함수
// ============================================================
function createShapeFromCoordinates(coords: number[][]) {
    const shape = new THREE.Shape();
    if (coords.length > 0) {
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

// ============================================================
// 컴포넌트: 매장 바닥/벽면
// ============================================================
function MapBoundary({ boundary }: { boundary: number[][] }) {
    const shape = useMemo(() => createShapeFromCoordinates(boundary), [boundary]);

    const extrudeSettings = { steps: 1, depth: 2.5, bevelEnabled: false };

    return (
        <group>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
                <shapeGeometry args={[shape]} />
                <meshStandardMaterial color="#E0E0E0" side={THREE.DoubleSide} />
            </mesh>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
                <extrudeGeometry args={[shape, extrudeSettings]} />
                <meshStandardMaterial color="#FAFAFA" transparent opacity={0.1} side={THREE.DoubleSide} />
            </mesh>
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

// ============================================================
// 컴포넌트: 선반 (반투명 처리)
// ============================================================
function PolygonShelf({ fixture }: { fixture: FixtureData }) {
    const shape = useMemo(() => createShapeFromCoordinates(fixture.geometry), [fixture.geometry]);

    const style = SHELF_STYLES[fixture.parentCategoryId] || { type: 'standard', color: '#9E9E9E' };

    // 중심점 계산
    const center = useMemo(() => {
        let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
        fixture.geometry.forEach(p => {
            if (p[0] < minX) minX = p[0];
            if (p[0] > maxX) maxX = p[0];
            if (p[1] < minZ) minZ = p[1];
            if (p[1] > maxZ) maxZ = p[1];
        });
        return [(minX + maxX) / 2, (minZ + maxZ) / 2];
    }, [fixture.geometry]);

    // 반투명 재질 설정
    const transparentMaterial = <meshStandardMaterial color={style.color} transparent opacity={0.3} depthWrite={false} />;
    const shelfBodyMaterial = <meshStandardMaterial color="#D7CCC8" transparent opacity={0.3} depthWrite={false} />;

    // 냉동고
    if (style.type === 'freezer') {
        return (
            <group>
                <mesh rotation={[-Math.PI / 2, 0, 0]} castShadow receiveShadow>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 1.0, bevelEnabled: false }]} />
                    <meshStandardMaterial color="#E1F5FE" transparent opacity={0.3} depthWrite={false} />
                </mesh>
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 1.01, 0]}>
                    <shapeGeometry args={[shape]} />
                    <meshStandardMaterial color="#81D4FA" transparent opacity={0.2} side={THREE.DoubleSide} />
                </mesh>
                {/* 테두리로 형태 강조 */}
                <lineSegments rotation={[-Math.PI / 2, 0, 0]} position={[0, 1.02, 0]}>
                    <edgesGeometry args={[new THREE.ShapeGeometry(shape)]} />
                    <lineBasicMaterial color={style.color} />
                </lineSegments>
                <ShelfLabel center={center} label={fixture.categoryName} subLabel={fixture.label} height={1.8} color="#5E35B1" />
            </group>
        );
    }

    // 냉장고
    if (style.type === 'refrigerator') {
        return (
            <group>
                <mesh rotation={[-Math.PI / 2, 0, 0]} castShadow>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 2.2, bevelEnabled: false }]} />
                    <meshStandardMaterial color="#E3F2FD" transparent opacity={0.3} depthWrite={false} />
                </mesh>
                {/* 선반 층 */}
                {[0.5, 1.0, 1.5].map((y, i) => (
                    <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, y, 0]}>
                        <shapeGeometry args={[shape]} />
                        <meshStandardMaterial color="#90CAF9" transparent opacity={0.1} />
                    </mesh>
                ))}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 2.2, 0]}>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.2, bevelEnabled: false }]} />
                    {transparentMaterial}
                </mesh>
                {/* 테두리 */}
                <lineSegments rotation={[-Math.PI / 2, 0, 0]} position={[0, 2.4, 0]}>
                    <edgesGeometry args={[new THREE.ShapeGeometry(shape)]} />
                    <lineBasicMaterial color={style.color} />
                </lineSegments>
                <ShelfLabel center={center} label={fixture.categoryName} subLabel={fixture.label} height={2.8} color={style.color} />
            </group>
        );
    }

    // 일반 선반
    const tiers = [0.4, 1.1, 1.8];
    return (
        <group>
            {tiers.map((y, i) => (
                <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, y, 0]} castShadow receiveShadow>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.1, bevelEnabled: false }]} />
                    {shelfBodyMaterial}
                </mesh>
            ))}
            {tiers.map((y, i) => (
                <mesh key={`prod-${i}`} rotation={[-Math.PI / 2, 0, 0]} position={[0, y + 0.1, 0]}>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.3, bevelEnabled: false }]} />
                    {transparentMaterial}
                </mesh>
            ))}
            {/* 상단 테두리 */}
            <lineSegments rotation={[-Math.PI / 2, 0, 0]} position={[0, 2.21, 0]}>
                <edgesGeometry args={[new THREE.ShapeGeometry(shape)]} />
                <lineBasicMaterial color={style.color} linewidth={1} />
            </lineSegments>
            <ShelfLabel center={center} label={fixture.categoryName} subLabel={fixture.label} height={2.5} color="#5D4037" />
        </group>
    );
}

function ShelfLabel({ center, label, subLabel, height, color }: { center: number[]; label: string; subLabel: string; height: number; color: string }) {
    return (
        <group position={[center[0], height, center[1]]}>
            <Text fontSize={0.4} color="white" anchorX="center" anchorY="bottom" outlineWidth={0.04} outlineColor="#000">
                {label}
            </Text>
            <Text position={[0, -0.45, 0]} fontSize={0.25} color={color} anchorX="center" anchorY="bottom" outlineWidth={0.02} outlineColor="#FFF">
                {subLabel}
            </Text>
        </group>
    );
}

// ============================================================
// 컴포넌트: 사용자 마커
// ============================================================
function UserMarker({ position }: { position: UserPosition }) {
    const threeX = position.x;
    const threeZ = -position.y;
    const rotationRad = -position.theta * (Math.PI / 180);

    return (
        <group position={[threeX, 0, threeZ]} rotation={[0, rotationRad, 0]}>
            <mesh position={[0, 0.4, 0]}>
                <sphereGeometry args={[0.3, 16, 16]} />
                <meshStandardMaterial color="#F44336" emissive="#EF9A9A" emissiveIntensity={0.5} />
            </mesh>
            <mesh position={[0, 0.4, -0.4]} rotation={[-Math.PI / 2, 0, 0]}>
                <coneGeometry args={[0.15, 0.3, 8]} />
                <meshStandardMaterial color="#F44336" />
            </mesh>
            <Text position={[0, 0.9, 0]} fontSize={0.3} color="white" outlineWidth={0.03} outlineColor="#000" anchorX="center">
                YOU
            </Text>
        </group>
    );
}

// ============================================================
// 컴포넌트: 카메라 리그 (3인칭 추적)
// ============================================================
function CameraRig({
    userPosition,
    isFollowing,
    setIsFollowing
}: {
    userPosition: UserPosition,
    isFollowing: boolean,
    setIsFollowing: (v: boolean) => void
}) {
    const { camera } = useThree();
    const controlsRef = useRef<OrbitControlsImpl>(null);

    useFrame(() => {
        if (isFollowing && controlsRef.current) {
            const threeX = userPosition.x;
            const threeZ = -userPosition.y;

            // 카메라 타겟 업데이트 (사용자 위치)
            controlsRef.current.target.set(threeX, 0, threeZ);

            // 카메라 위치 업데이트 (3인칭 시점: 뒤 4m, 위 6m)
            // 사용자 바라보는 방향 (theta) 기준
            // theta는 0도가 North(Z-?) 라고 가정하거나 데이터에 따라 다름.
            // 여기서는 단순히 고정된 오프셋을 사용하거나, theta를 반영할 수 있음.
            // 사용자 theta를 라디안으로 변환 (UserMarker 참조: -theta * PI/180)
            const rotationRad = -userPosition.theta * (Math.PI / 180);

            // 3인칭 숄더뷰 (TPS 느낌: 적당히 뒤에서 내려다보기)
            // 너비/높이를 좀 더 확보하여 주변 상황 파악 용이
            const height = 2.5;
            const dist = 2.0;

            // 3인칭 쿼터뷰 (Top-down 약간 뒤)
            // 사용자 뒤(0,0,1) * 회전
            const backVector = new THREE.Vector3(0, height, dist).applyAxisAngle(new THREE.Vector3(0, 1, 0), rotationRad);

            // 부드러운 이동 (Lerp)
            const targetPos = new THREE.Vector3(threeX, 0, threeZ).add(backVector);

            camera.position.lerp(targetPos, 0.1);
            controlsRef.current.update();
        }
    });

    return (
        <OrbitControls
            ref={controlsRef}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            onStart={() => {
                // 사용자가 조작을 시작하면 팔로우 모드 해제
                if (isFollowing) setIsFollowing(false);
            }}
        />
    );
}

// ============================================================
// 컴포넌트: 씬
// ============================================================
function StoreScene({
    mapData,
    userPosition,
    isFollowing,
    setIsFollowing,
    navigationPath
}: {
    mapData: MapDataResponse;
    userPosition: UserPosition;
    isFollowing: boolean;
    setIsFollowing: (v: boolean) => void;
    navigationPath?: number[][] | null;
}) {
    return (
        <>
            <ambientLight intensity={0.6} />
            <directionalLight position={[10, 20, 5]} intensity={0.8} castShadow />
            <hemisphereLight args={['#ffffff', '#444444', 0.4]} />

            <MapBoundary boundary={mapData.storeMap.boundary} />

            {mapData.fixtures.map((fixture) => (
                <PolygonShelf key={fixture.id} fixture={fixture} />
            ))}

            <UserMarker position={userPosition} />

            {/* 내비게이션 경로 */}
            <NavigationPath path={navigationPath || null} />

            {/* 카메라 리그 */}
            <CameraRig
                userPosition={userPosition}
                isFollowing={isFollowing}
                setIsFollowing={setIsFollowing}
            />

            <gridHelper args={[50, 50, '#EEEEEE', '#EEEEEE']} position={[0, -0.1, 0]} />
        </>
    );
}

// ============================================================
// 메인 컴포넌트
// ============================================================
export default function StoreMap({ className = '', navigationPath }: StoreMapProps) {
    const [mapData, setMapData] = useState<MapDataResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [pos, setPos] = useState<UserPosition>({ x: 0.06, y: 0.11, theta: 18.5 });
    const [isFollowing, setIsFollowing] = useState(true); // 팔로우 모드 상태

    // API에서 지도 데이터 가져오기
    useEffect(() => {
        async function fetchMapData() {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8123';
            console.log('[StoreMap] API 요청 시작:', `${apiUrl}/api/map`);

            try {
                const response = await fetch(`${apiUrl}/api/map`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data: MapDataResponse = await response.json();
                setMapData(data);
            } catch (err) {
                console.error('[StoreMap] API 요청 실패:', err);
                setError(err instanceof Error ? err.message : '지도 데이터 로드 실패');
            } finally {
                setLoading(false);
            }
        }
        fetchMapData();
    }, []);

    // 실시간 위치 SSE 스트림 구독
    useEffect(() => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8123';
        const url = `${apiUrl}/api/map/position/stream`;

        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setPos({
                    x: data.x,
                    y: data.y,
                    theta: data.theta
                });
            } catch (err) {
                console.error('[StoreMap] 위치 데이터 파싱 실패:', err);
            }
        };

        return () => {
            eventSource.close();
        };
    }, []);

    // 로딩 화면
    if (loading) {
        return (
            <div className={`w-full h-full bg-gray-900 rounded-lg flex items-center justify-center ${className}`}>
                <div className="text-white text-lg">지도 로딩 중...</div>
            </div>
        );
    }

    // 에러 화면
    if (error || !mapData) {
        return (
            <div className={`w-full h-full bg-gray-900 rounded-lg flex items-center justify-center ${className}`}>
                <div className="text-red-400 text-lg">⚠️ {error || '지도 데이터 없음'}</div>
            </div>
        );
    }

    return (
        <div className={`relative w-full h-full bg-gray-900 rounded-lg overflow-hidden ${className}`}>
            {/* 디버그 오버레이 (삭제 가능) */}
            {/* <div className="absolute top-4 left-4 z-10 bg-black/50 text-white p-2 rounded text-xs pointer-events-none">
                <p>User: {pos.x.toFixed(2)}, {pos.y.toFixed(2)}</p>
                <p>Theta: {pos.theta.toFixed(1)}°</p>
            </div> */}

            {/* 팔로우 모드 토글 버튼 */}
            {!isFollowing && (
                <button
                    onClick={() => setIsFollowing(true)}
                    className="absolute top-4 right-4 z-20 bg-white/10 hover:bg-white/20 backdrop-blur-md text-white p-2 rounded-full shadow-lg transition-all border border-white/20"
                    title="내 위치 따라가기"
                    aria-label="Follow user"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                </button>
            )}

            <Canvas shadows>
                <StoreScene
                    mapData={mapData}
                    userPosition={pos}
                    isFollowing={isFollowing}
                    setIsFollowing={setIsFollowing}
                    navigationPath={navigationPath}
                />
            </Canvas>
        </div>
    );
}

