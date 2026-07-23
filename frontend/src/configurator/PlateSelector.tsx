import type { GangCount } from "./assemblyTypes";
import { SUPPORTED_GANG_COUNTS } from "./assemblyTypes";

interface PlateSelectorProps {
  value: GangCount;
  onChange: (gangCount: GangCount) => void;
  disabled?: boolean;
}

export function PlateSelector({
  value,
  onChange,
  disabled,
}: PlateSelectorProps) {
  return (
    <fieldset className="option-group" disabled={disabled}>
      <legend className="option-label">Plate Gangs</legend>
      <div
        className="segmented segmented-row-4"
        role="radiogroup"
        aria-label="Plate gang count"
      >
        {SUPPORTED_GANG_COUNTS.map((gangCount) => {
          const selected = gangCount === value;
          return (
            <button
              key={gangCount}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-pressed={selected}
              aria-label={`${gangCount} gang`}
              className={`segmented-button${selected ? " is-active" : ""}`}
              onClick={() => onChange(gangCount)}
              disabled={disabled}
            >
              {gangCount}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
