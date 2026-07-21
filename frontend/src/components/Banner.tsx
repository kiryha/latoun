// Inline status banner for error and success messages.

interface BannerProps {
  kind: "error" | "success";
  children: React.ReactNode;
  onDismiss?: () => void;
}

export function Banner({ kind, children, onDismiss }: BannerProps) {
  return (
    <div className={`banner banner-${kind}`} role="alert">
      <span>{children}</span>
      {onDismiss && (
        <button type="button" className="banner-close" onClick={onDismiss}>
          ×
        </button>
      )}
    </div>
  );
}
