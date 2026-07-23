interface FinishOption {
  code: string;
  label: string;
}

interface FinishSelectorProps {
  value: string;
  options: FinishOption[];
  onChange: (finishSchemeCode: string) => void;
  disabled?: boolean;
}

export function FinishSelector({
  value,
  options,
  onChange,
  disabled,
}: FinishSelectorProps) {
  return (
    <fieldset className="option-group" disabled={disabled}>
      <legend className="option-label">Finish</legend>
      <div
        className="segmented"
        role="radiogroup"
        aria-label="Assembly finish"
      >
        {options.map((option) => {
          const selected = option.code === value;
          return (
            <button
              key={option.code}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-pressed={selected}
              className={`segmented-button${selected ? " is-active" : ""}`}
              onClick={() => onChange(option.code)}
              disabled={disabled}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
