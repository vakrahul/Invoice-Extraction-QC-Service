import React, { Suspense, useRef } from 'react';
import { Canvas, useLoader, useFrame } from '@react-three/fiber';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { OrbitControls, Html } from '@react-three/drei';

// CRITICAL PATH CHECK: The asset MUST be in frontend/public/
// If your file is named differently, update this string.
const ModelPath = '/invoice.glb'; 

function Scene() {
    // 1. Load the GLB asset
    // We use a try/catch pattern here in case the file is corrupted.
    try {
        const gltf = useLoader(GLTFLoader, ModelPath);
        const meshRef = useRef();
        
        // Continuous rotation for animation
        useFrame((state, delta) => {
            if (meshRef.current) {
                meshRef.current.rotation.y += delta * 0.5;
            }
        });

        return (
            <primitive 
                ref={meshRef}
                object={gltf.scene} 
                scale={0.015} // Scale adjusted for viewing
                position={[0, 0, 0]} 
            />
        );
    } catch (error) {
        // Fallback to simple box if GLB file load fails entirely
        return (
            <mesh position={[0, 0, 0]}>
                <boxGeometry args={[1, 1, 1]} />
                <meshStandardMaterial color="#f00" /> {/* Red Error Box */}
            </mesh>
        );
    }
}

function ModelViewer({ isLoading, isVisible }) {
    return (
        <div style={{ 
            height: '400px', 
            width: '100%', 
            backgroundColor: isVisible ? '#f7f7f7' : 'transparent',
            borderRadius: '8px',
            border: isVisible ? '1px solid #ddd' : 'none',
            display: isVisible ? 'block' : 'none',
            overflow: 'hidden'
        }}>
            <Canvas camera={{ position: [0, 0, 4], fov: 60 }}>
                <ambientLight intensity={1.5} />
                <directionalLight position={[10, 10, 5]} intensity={1.5} />
                
                <Suspense fallback={
                     <Html center>
                        <div style={{ color: '#3b82f6', fontWeight: 'bold' }}>
                            {isLoading ? 'Processing Document...' : 'Loading 3D View...'}
                        </div>
                    </Html>
                }>
                    <Scene />
                </Suspense>
                
                <OrbitControls enableZoom={true} />
            </Canvas>
        </div>
    );
}

export default ModelViewer;