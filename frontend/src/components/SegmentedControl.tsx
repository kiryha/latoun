// A simple segmented button group used for the device and material selectors.

interface Option {
  code: string;
  label: string;
}

interface SegmentedControlProps {
  options: Option[];
  value: string;
  onChange: (code: string) => void;
  disabled?: boolean;
}

export function SegmentedControl({
  options,
  value,
  onChange,
  disabled,
}: SegmentedControlProps) {
  return (
    <div className="segmented">
      {options.map((option) => (
        <button
          key={option.code}
          type="button"
          className={`segmented-button${option.code === value ? " is-active" : ""}`}
          onClick={() => onChange(option.code)}
          disabled={disabled}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
