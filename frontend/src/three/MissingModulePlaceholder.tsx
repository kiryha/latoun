// Neutral placeholder for slots whose GLB is not yet registered.
// Distinct from the magenta missing-material shader.

import { Html } from "@react-three/drei";

interface MissingModulePlaceholderProps {
  slotNumber: number;
  moduleType: string;
  offsetX?: number;
}

export function MissingModulePlaceholder({
  slotNumber,
  moduleType,
  offsetX = 0,
}: MissingModulePlaceholderProps) {
  const label = `Slot ${slotNumber}\n${moduleType.split("_").join(" ")}\nmissing asset`;

  return (
    <group name={`Slot_${slotNumber}_Placeholder`}>
      <mesh position={[offsetX, 0, 0]}>
        <boxGeometry args={[0.045, 0.07, 0.02]} />
        <meshStandardMaterial color="#6b727a" roughness={0.85} metalness={0.05} />
      </mesh>
      <Html position={[offsetX, 0.055, 0]} center distanceFactor={0.35}>
        <div className="missing-asset-label">{label}</div>
      </Html>
    </group>
  );
}
