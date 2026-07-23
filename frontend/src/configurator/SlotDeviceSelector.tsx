import type { ModuleTypeCode, ModuleTypeOption } from "./assemblyTypes";
import { isModuleTypeCode } from "./assemblyConfigurationService";

interface SlotDeviceSelectorProps {
  slotNumber: number;
  value: ModuleTypeCode;
  options: ModuleTypeOption[];
  onChange: (slotNumber: number, moduleTypeCode: ModuleTypeCode) => void;
  disabled?: boolean;
}

export function SlotDeviceSelector({
  slotNumber,
  value,
  options,
  onChange,
  disabled,
}: SlotDeviceSelectorProps) {
  const selectId = `slot-${slotNumber}-device`;

  return (
    <div className="slot-device">
      <label className="slot-device-label" htmlFor={selectId}>
        Slot {slotNumber}
      </label>
      <select
        id={selectId}
        className="text-input slot-device-select"
        aria-label={`Select device for slot ${slotNumber}`}
        value={value}
        disabled={disabled}
        onChange={(event) => {
          const next = event.target.value;
          if (isModuleTypeCode(next)) {
            onChange(slotNumber, next);
          }
        }}
      >
        {options.map((option) => (
          <option key={option.code} value={option.code}>
            {option.displayName}
          </option>
        ))}
      </select>
    </div>
  );
}
