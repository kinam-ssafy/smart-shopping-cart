'use client';

import { useEffect, useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Text } from '@react-three/drei';
import * as THREE from 'three';

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
                <meshStandardMaterial color="#FAFAFA" transparent opacity={0.3} side={THREE.DoubleSide} />
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
// 컴포넌트: 선반
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

    // 냉동고
    if (style.type === 'freezer') {
        return (
            <group>
                <mesh rotation={[-Math.PI / 2, 0, 0]} castShadow receiveShadow>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 1.0, bevelEnabled: false }]} />
                    <meshStandardMaterial color="#E1F5FE" />
                </mesh>
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 1.01, 0]}>
                    <shapeGeometry args={[shape]} />
                    <meshStandardMaterial color="#81D4FA" transparent opacity={0.5} side={THREE.DoubleSide} />
                </mesh>
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
                    <meshStandardMaterial color="#E3F2FD" transparent opacity={0.8} />
                </mesh>
                {[0.5, 1.0, 1.5].map((y, i) => (
                    <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, y, 0]}>
                        <shapeGeometry args={[shape]} />
                        <meshStandardMaterial color="#90CAF9" />
                    </mesh>
                ))}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 2.2, 0]}>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.2, bevelEnabled: false }]} />
                    <meshStandardMaterial color={style.color} />
                </mesh>
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
                    <meshStandardMaterial color="#D7CCC8" />
                </mesh>
            ))}
            {tiers.map((y, i) => (
                <mesh key={`prod-${i}`} rotation={[-Math.PI / 2, 0, 0]} position={[0, y + 0.1, 0]}>
                    <extrudeGeometry args={[shape, { steps: 1, depth: 0.3, bevelEnabled: false }]} />
                    <meshStandardMaterial color={style.color} />
                </mesh>
            ))}
            <ShelfLabel center={center} label={fixture.categoryName} subLabel={fixture.label} height={2.5} color="#5D4037" />
        </group>
    );
}

function ShelfLabel({ center, label, subLabel, height, color }: { center: number[]; label: string; subLabel: string; height: number; color: string }) {
    return (
        <group position={[center[0], height, -center[1]]}>
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
// 컴포넌트: 씬
// ============================================================
function StoreScene({ mapData, userPosition }: { mapData: MapDataResponse; userPosition: UserPosition }) {
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

            <OrbitControls enablePan enableZoom enableRotate target={[2, 0, -7]} />
            <PerspectiveCamera makeDefault position={[5, 15, 10]} fov={50} />
            <gridHelper args={[50, 50, '#EEEEEE', '#EEEEEE']} position={[0, -0.1, 0]} />
        </>
    );
}

// ============================================================
// 메인 컴포넌트
// ============================================================
export default function StoreMap({ className = '' }: StoreMapProps) {
    const [mapData, setMapData] = useState<MapDataResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [pos, setPos] = useState<UserPosition>({ x: 0.06, y: 0.11, theta: 18.5 });

    // API에서 지도 데이터 가져오기
    useEffect(() => {
        async function fetchMapData() {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8123';
                const response = await fetch(`${apiUrl}/api/map`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data: MapDataResponse = await response.json();
                setMapData(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : '지도 데이터 로드 실패');
            } finally {
                setLoading(false);
            }
        }
        fetchMapData();
    }, []);

    // 실시간 위치 시뮬레이션
    useEffect(() => {
        const interval = setInterval(() => {
            setPos((prev: UserPosition) => {
                const time = Date.now() / 1000;
                const radius = 3;
                const newX = Math.cos(time) * radius;
                const newY = 3 + Math.sin(time) * radius;
                const newTheta = Math.atan2(Math.cos(time), -Math.sin(time)) * 180 / Math.PI;
                return { x: Number(newX.toFixed(2)), y: Number(newY.toFixed(2)), theta: Number(newTheta.toFixed(1)) };
            });
        }, 100);
        return () => clearInterval(interval);
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
        <div className={`w-full h-full bg-gray-900 rounded-lg overflow-hidden ${className}`}>
            <div className="absolute top-4 left-4 z-10 bg-black/50 text-white p-2 rounded text-xs">
                <p>User Position JSON:</p>
                <pre>{JSON.stringify(pos, null, 2)}</pre>
            </div>
            <Canvas shadows>
                <StoreScene mapData={mapData} userPosition={pos} />
            </Canvas>
        </div>
    );
}
