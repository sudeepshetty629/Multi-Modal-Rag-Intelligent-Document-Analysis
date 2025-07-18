import React, { useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';

function NeuralNetwork() {
  const ref = useRef();
  const count = 2000;
  
  const [positions, colors] = React.useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      const x = (Math.random() - 0.5) * 20;
      const y = (Math.random() - 0.5) * 20;
      const z = (Math.random() - 0.5) * 20;
      
      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
      
      // Purple gradient colors
      colors[i * 3] = 0.8 + Math.random() * 0.2;     // Red
      colors[i * 3 + 1] = 0.3 + Math.random() * 0.3; // Green
      colors[i * 3 + 2] = 1.0;                       // Blue
    }
    
    return [positions, colors];
  }, [count]);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    ref.current.rotation.x = time * 0.1;
    ref.current.rotation.y = time * 0.05;
  });

  return (
    <group ref={ref}>
      <Points positions={positions} colors={colors} stride={3}>
        <PointMaterial
          transparent
          color="#e935ff"
          size={0.05}
          sizeAttenuation={true}
          depthWrite={false}
          vertexColors={true}
          blending={THREE.AdditiveBlending}
        />
      </Points>
    </group>
  );
}

function FloatingOrbs() {
  return (
    <>
      {[...Array(5)].map((_, i) => (
        <Float key={i} speed={1 + i * 0.2} rotationIntensity={0.5} floatIntensity={0.5}>
          <mesh position={[Math.random() * 10 - 5, Math.random() * 10 - 5, Math.random() * 10 - 5]}>
            <sphereGeometry args={[0.3, 32, 32]} />
            <meshStandardMaterial
              color="#667eea"
              transparent
              opacity={0.1}
              emissive="#667eea"
              emissiveIntensity={0.1}
            />
          </mesh>
        </Float>
      ))}
    </>
  );
}

const NeuralBackground = () => {
  return (
    <div className="fixed inset-0 w-full h-full -z-10">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 60 }}
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <NeuralNetwork />
        <FloatingOrbs />
      </Canvas>
      
      {/* Overlay gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-neural-900/90 via-neural-900/50 to-neural-800/90 pointer-events-none" />
    </div>
  );
};

export default NeuralBackground;