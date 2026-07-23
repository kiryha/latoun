import type {
  AssemblySlotConfiguration,
  ModuleTypeCode,
  ModuleTypeOption,
} from "./assemblyTypes";
import { SlotDeviceSelector } from "./SlotDeviceSelector";

interface SlotDeviceListProps {
  slots: AssemblySlotConfiguration[];
  options: ModuleTypeOption[];
  onChange: (slotNumber: number, moduleTypeCode: ModuleTypeCode) => void;
  disabled?: boolean;
}

export function SlotDeviceList({
  slots,
  options,
  onChange,
  disabled,
}: SlotDeviceListProps) {
  return (
    <section className="option-group">
      <h3 className="option-label">Devices</h3>
      <div className="slot-device-list">
        {[...slots]
          .sort((a, b) => a.slotNumber - b.slotNumber)
          .map((slot) => (
            <SlotDeviceSelector
              key={slot.slotNumber}
              slotNumber={slot.slotNumber}
              value={slot.moduleTypeCode}
              options={options}
              onChange={onChange}
              disabled={disabled}
            />
          ))}
      </div>
    </section>
  );
}
