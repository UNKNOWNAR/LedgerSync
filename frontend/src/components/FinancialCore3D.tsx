import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Html, Sparkles, MeshWobbleMaterial } from '@react-three/drei'
import * as THREE from 'three'

// ─── Constants ───────────────────────────────────────────────────────────────
const CYCLE = 6.5   // seconds per full lane cycle
const START_X = 7.0 // home x position for each side

// ─── Lane definitions ────────────────────────────────────────────────────────
const LANES = [
  { y:  2.6, gwAmt: '$1,240.00', bkAmt: '$1,240.00', matched: true,  gwLabel: 'STRIPE_API',  bkLabel: 'HSBC_7A2F', phaseOffset: 0.00 },
  { y:  1.2, gwAmt: '$842.50',   bkAmt: '$842.50',   matched: true,  gwLabel: 'PAYPAL_MX',   bkLabel: 'CITI_3D9C', phaseOffset: 0.18 },
  { y: -0.1, gwAmt: '$3,180.00', bkAmt: '$3,180.00', matched: true,  gwLabel: 'ADYEN_EU',    bkLabel: 'BARO_8E1B', phaseOffset: 0.36 },
  { y: -1.4, gwAmt: '$95.00',    bkAmt: '$97.50',    matched: false, gwLabel: 'SQUARE_US',   bkLabel: 'WELLS_2FA', phaseOffset: 0.54 },
  { y: -2.8, gwAmt: '$2,050.00', bkAmt: '$2,050.00', matched: true,  gwLabel: 'BRAINTREE',   bkLabel: 'JPMC_5C8D', phaseOffset: 0.72 },
]

// ─── Easing ──────────────────────────────────────────────────────────────────
function easeInOut3(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}
function easeOut3(t: number) {
  return 1 - Math.pow(1 - t, 3)
}

// ─── 1. Refined Lane component with Translucent Glass Chips & Optical Nodes ────
function LanePair({
  y, gwAmt, bkAmt, matched, gwLabel, bkLabel, phaseOffset,
}: typeof LANES[0]) {
  const gwRef    = useRef<THREE.Group>(null)
  const bkRef    = useRef<THREE.Group>(null)
  const gwMat    = useRef<THREE.MeshBasicMaterial>(null)
  const bkMat    = useRef<THREE.MeshBasicMaterial>(null)
  const gwHalo   = useRef<THREE.MeshBasicMaterial>(null)
  const bkHalo   = useRef<THREE.MeshBasicMaterial>(null)
  const connMesh = useRef<THREE.Mesh>(null)
  const connMat  = useRef<THREE.MeshBasicMaterial>(null)

  const gwColor = useMemo(() => new THREE.Color(matched ? '#4DA3FF' : '#F59E0B'), [matched])
  const bkColor = useMemo(() => new THREE.Color(matched ? '#00BFA6' : '#EF4444'), [matched])

  useFrame((state) => {
    const elapsed = state.clock.elapsedTime
    const t = ((elapsed / CYCLE) + phaseOffset) % 1

    let gwX = -START_X, gwY = 0
    let bkX =  START_X, bkY = 0
    let gwOp = 0.85, bkOp = 0.85
    let gwHaloOp = 0.09, bkHaloOp = 0.09
    let connOp = 0

    if (t < 0.25) {
      // Idle — gentle breathing pulse
      const pulse = 0.55 + Math.sin(elapsed * 1.8 + phaseOffset * 12) * 0.2
      gwOp = bkOp = pulse
      gwHaloOp = bkHaloOp = pulse * 0.14

    } else if (t < 0.60) {
      // Approach
      const p = easeInOut3((t - 0.25) / 0.35)
      gwX = THREE.MathUtils.lerp(-START_X, 0, p)
      bkX = THREE.MathUtils.lerp( START_X, 0, p)
      gwOp = bkOp = 0.9
      gwHaloOp = bkHaloOp = 0.13
      connOp = matched ? p * 0.18 : 0

    } else if (t < 0.72) {
      // At center
      const p = (t - 0.60) / 0.12
      gwX = matched ? 0 : -0.35
      bkX = matched ? 0 :  0.35
      const flash = matched
        ? 0.7 + Math.sin(p * Math.PI * 7) * 0.3
        : 0.20 + Math.sin(p * Math.PI * 3) * 0.08
      gwOp = bkOp = flash
      gwHaloOp = bkHaloOp = matched ? flash * 0.5 : 0.04
      connOp = matched ? (0.14 + Math.sin(p * Math.PI * 7) * 0.65) : 0

    } else if (t < 0.90) {
      // Exit
      const p = easeOut3((t - 0.72) / 0.18)
      if (matched) {
        gwX = bkX = -p * 4.5
        gwY = bkY = -p * 1.5
      } else {
        gwX = -p * START_X * 0.9
        bkX =  p * START_X * 0.9
        gwY =  p * 1.4
        bkY = -p * 1.4
      }
      gwOp = bkOp = 1 - p
      gwHaloOp = bkHaloOp = (1 - p) * 0.12
      connOp = matched ? (1 - p) * 0.45 : 0

    } else {
      // Fade in at home
      const fp = (t - 0.90) / 0.10
      gwOp = bkOp = fp * 0.55
      gwHaloOp = bkHaloOp = fp * 0.07
    }

    const clamp = (v: number) => Math.max(0, Math.min(1, v))

    if (gwRef.current)  { gwRef.current.position.x = gwX; gwRef.current.position.y = gwY }
    if (bkRef.current)  { bkRef.current.position.x = bkX; bkRef.current.position.y = bkY }
    if (gwMat.current)  gwMat.current.opacity  = clamp(gwOp)
    if (bkMat.current)  bkMat.current.opacity  = clamp(bkOp)
    if (gwHalo.current) gwHalo.current.opacity  = clamp(gwHaloOp)
    if (bkHalo.current) bkHalo.current.opacity  = clamp(bkHaloOp)

    // Connector beam scaling
    if (connMesh.current && connMat.current) {
      const dist  = Math.abs(bkX - gwX)
      const midX  = (gwX + bkX) / 2
      const midY  = (gwY + bkY) / 2
      connMesh.current.scale.x    = Math.max(0.001, dist)
      connMesh.current.position.x = midX
      connMesh.current.position.y = midY
      connMat.current.opacity     = clamp(connOp)
    }
  })

  // Translucent edge-lit HUD data chips styling
  const gwStyle: React.CSSProperties = {
    transform: 'translateX(calc(-100% - 14px))',
    padding: '4px 10px',
    borderRadius: 8,
    background: 'rgba(10, 14, 22, 0.78)',
    border: `1px solid ${matched ? 'rgba(77, 163, 255, 0.28)' : 'rgba(245, 158, 11, 0.28)'}`,
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
    fontSize: '0.6rem',
    fontFamily: 'JetBrains Mono, monospace',
    color: matched ? '#4DA3FF' : '#F59E0B',
    whiteSpace: 'nowrap',
    pointerEvents: 'none',
    textAlign: 'right',
    lineHeight: 1.35,
  }

  const bkStyle: React.CSSProperties = {
    transform: 'translateX(14px)',
    padding: '4px 10px',
    borderRadius: 8,
    background: 'rgba(10, 14, 22, 0.78)',
    border: `1px solid ${matched ? 'rgba(0, 191, 166, 0.28)' : 'rgba(239, 68, 68, 0.28)'}`,
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
    fontSize: '0.6rem',
    fontFamily: 'JetBrains Mono, monospace',
    color: matched ? '#00BFA6' : '#EF4444',
    whiteSpace: 'nowrap',
    pointerEvents: 'none',
    lineHeight: 1.35,
  }

  const subStyle: React.CSSProperties = {
    fontSize: '0.48rem',
    opacity: 0.55,
    letterSpacing: '0.08em',
    marginBottom: 2,
    fontWeight: 600,
  }

  return (
    <group position={[0, y, 0]}>
      {/* ── Gateway node (from left) ── */}
      <group ref={gwRef}>
        <mesh>
          <sphereGeometry args={[0.15, 24, 24]} />
          <meshBasicMaterial ref={gwMat} color={gwColor} transparent depthWrite={false} blending={THREE.AdditiveBlending} />
        </mesh>
        {/* Optical Glow Halo */}
        <mesh>
          <sphereGeometry args={[0.38, 16, 16]} />
          <meshBasicMaterial ref={gwHalo} color={gwColor} transparent depthWrite={false} blending={THREE.AdditiveBlending} />
        </mesh>
        <Html center>
          <div style={gwStyle}>
            <div style={subStyle}>{gwLabel}</div>
            <div style={{ fontWeight: 700 }}>{gwAmt}</div>
          </div>
        </Html>
      </group>

      {/* ── Bank node (from right) ── */}
      <group ref={bkRef}>
        <mesh>
          <sphereGeometry args={[0.15, 24, 24]} />
          <meshBasicMaterial ref={bkMat} color={bkColor} transparent depthWrite={false} blending={THREE.AdditiveBlending} />
        </mesh>
        <mesh>
          <sphereGeometry args={[0.38, 16, 16]} />
          <meshBasicMaterial ref={bkHalo} color={bkColor} transparent depthWrite={false} blending={THREE.AdditiveBlending} />
        </mesh>
        <Html center>
          <div style={bkStyle}>
            <div style={subStyle}>{bkLabel}</div>
            <div style={{ fontWeight: 700 }}>{bkAmt}</div>
          </div>
        </Html>
      </group>

      {/* ── Refined Laser Connection Beam ── */}
      <mesh ref={connMesh} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.012, 0.012, 1, 8]} />
        <meshBasicMaterial
          ref={connMat}
          color={matched ? '#00BFA6' : '#EF4444'}
          transparent
          opacity={0}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  )
}

// ─── 2. Multi-Layered Physical Glass Match Engine ─────────────────────────────
function MatchingEngine() {
  const coreRef    = useRef<THREE.Mesh>(null)
  const ringRef    = useRef<THREE.Group>(null)
  const innerGlow  = useRef<THREE.MeshBasicMaterial>(null)
  const outerGlow  = useRef<THREE.MeshBasicMaterial>(null)

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime
    if (coreRef.current) coreRef.current.rotation.y += delta * 0.4
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 0.3
      ringRef.current.rotation.x -= delta * 0.2
    }
    const pulse = 0.5 + Math.sin(t * 2.2) * 0.2
    if (innerGlow.current) innerGlow.current.opacity = pulse * 0.42
    if (outerGlow.current) outerGlow.current.opacity = pulse * 0.09
  })

  const headerStyle = (color: string, align?: 'left' | 'right' | 'center'): React.CSSProperties => ({
    fontSize: '0.52rem',
    fontFamily: 'JetBrains Mono, monospace',
    color,
    letterSpacing: '0.14em',
    textTransform: 'uppercase',
    opacity: 0.65,
    pointerEvents: 'none',
    whiteSpace: 'nowrap',
    textAlign: align ?? 'center',
    fontWeight: 700,
  })

  return (
    <group>
      {/* Vertical Axis Specular Line */}
      <mesh>
        <cylinderGeometry args={[0.006, 0.006, 7.2, 8]} />
        <meshBasicMaterial color="#2F80FF" transparent opacity={0.2} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      {/* Ticks at lane heights */}
      {LANES.map((lane, i) => (
        <mesh key={i} position={[0, lane.y, 0]}>
          <boxGeometry args={[0.26, 0.006, 0.006]} />
          <meshBasicMaterial color="#2F80FF" transparent opacity={0.28} blending={THREE.AdditiveBlending} depthWrite={false} />
        </mesh>
      ))}

      {/* Outer Physical Glass Housing */}
      <mesh>
        <icosahedronGeometry args={[0.42, 4]} />
        <meshPhysicalMaterial
          roughness={0.05}
          metalness={0.2}
          transmission={0.92}
          thickness={1.2}
          color="#0B0F17"
          clearcoat={1.0}
          clearcoatRoughness={0.04}
          ior={1.5}
        />
      </mesh>

      {/* Inner Glowing AI Core Sphere */}
      <mesh ref={coreRef}>
        <sphereGeometry args={[0.22, 32, 32]} />
        <MeshWobbleMaterial
          color="#2F80FF"
          emissive="#00BFA6"
          emissiveIntensity={1.2}
          factor={0.4}
          speed={2.0}
          roughness={0.1}
          metalness={0.8}
        />
      </mesh>

      {/* Orbital Wireframe Ring */}
      <group ref={ringRef}>
        <mesh>
          <torusGeometry args={[0.65, 0.008, 16, 80]} />
          <meshBasicMaterial color="#4DA3FF" transparent opacity={0.4} blending={THREE.AdditiveBlending} depthWrite={false} />
        </mesh>
      </group>

      {/* Inner & Outer Volumetric Glow */}
      <mesh>
        <sphereGeometry args={[0.55, 16, 16]} />
        <meshBasicMaterial ref={innerGlow} color="#2F80FF" transparent opacity={0.35} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      <mesh>
        <sphereGeometry args={[1.25, 12, 12]} />
        <meshBasicMaterial ref={outerGlow} color="#2F80FF" transparent opacity={0.08} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      {/* Column headers */}
      <Html position={[-START_X, 3.65, 0]} center>
        <div style={headerStyle('#4DA3FF')}>Payment Gateway</div>
      </Html>
      <Html position={[0, 3.65, 0]} center>
        <div style={{ ...headerStyle('#60CFFF'), opacity: 0.8 }}>AI Engine</div>
      </Html>
      <Html position={[START_X, 3.65, 0]} center>
        <div style={headerStyle('#00BFA6')}>Bank Statement</div>
      </Html>
    </group>
  )
}

// ─── 3. Studio Lighting & Mouse Parallax Scene ─────────────────────────────────
function SceneContent() {
  const groupRef = useRef<THREE.Group>(null)

  useFrame((state) => {
    if (!groupRef.current) return
    groupRef.current.rotation.y = THREE.MathUtils.lerp(
      groupRef.current.rotation.y,
      state.mouse.x * 0.10,
      0.032,
    )
    groupRef.current.rotation.x = THREE.MathUtils.lerp(
      groupRef.current.rotation.x,
      -state.mouse.y * 0.06,
      0.032,
    )
  })

  return (
    <group ref={groupRef}>
      {/* Studio Lighting Setup */}
      <ambientLight intensity={0.35} />
      <directionalLight position={[10, 14, 8]} intensity={2.2} color="#4DA3FF" />
      <pointLight position={[-9, 0, 4]} intensity={1.2} color="#4DA3FF" />
      <pointLight position={[9, 0, 4]} intensity={1.0} color="#00BFA6" />
      <pointLight position={[0, 0, 7]} intensity={0.5} color="#ffffff" />

      <MatchingEngine />
      {LANES.map((lane, i) => <LanePair key={i} {...lane} />)}

      <Sparkles
        count={140}
        scale={[24, 8, 8]}
        size={1.1}
        speed={0.2}
        opacity={0.25}
        color="#4DA3FF"
      />
    </group>
  )
}

// ─── Export ───────────────────────────────────────────────────────────────────
export default function FinancialCore3D() {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Canvas
        camera={{ position: [0, 0, 13], fov: 48 }}
        gl={{ alpha: true, antialias: true, powerPreference: 'high-performance' }}
      >
        <SceneContent />
      </Canvas>
    </div>
  )
}
