interface AsyncStatusProps {
  busy: boolean;
  statusText: string | null;
  error: string | null;
}

export function AsyncStatus({ busy, statusText, error }: AsyncStatusProps) {
  return (
    <>
      <div className="mt-3 flex items-center gap-2">
        {busy && (
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-warm-gray/30 border-t-terracotta"
            role="status"
            aria-label="Loading"
          />
        )}
        <p className="text-sm text-warm-gray">{statusText}</p>
      </div>
      {error && <p className="mt-3 text-sm text-rust">{error}</p>}
    </>
  );
}
