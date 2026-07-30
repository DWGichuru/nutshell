import { useEffect, useRef } from 'react';
import { nextPollAction, type PollableStatus } from '../lib/polling';

interface UsePollingOptions<T extends PollableStatus> {
  key: string | null;
  intervalMs?: number;
  fetchStatus: (key: string) => Promise<T>;
  onDone: (status: T) => void;
  onError: (status: T) => void;
}

export function usePolling<T extends PollableStatus>({
  key,
  intervalMs = 2000,
  fetchStatus,
  onDone,
  onError,
}: UsePollingOptions<T>): void {
  const fetchStatusRef = useRef(fetchStatus);
  const onDoneRef = useRef(onDone);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    fetchStatusRef.current = fetchStatus;
    onDoneRef.current = onDone;
    onErrorRef.current = onError;
  });

  useEffect(() => {
    if (key === null) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    async function poll() {
      let status: T;
      try {
        status = await fetchStatusRef.current(key!);
      } catch (err) {
        if (cancelled) return;
        onErrorRef.current({
          status: 'error',
          error: err instanceof Error ? err.message : 'Request failed.',
        } as T);
        return;
      }
      if (cancelled) return;

      const action = nextPollAction(status);
      if (action === 'done') {
        onDoneRef.current(status);
        return;
      }
      if (action === 'error') {
        onErrorRef.current(status);
        return;
      }
      timeoutId = setTimeout(poll, intervalMs);
    }

    poll();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [key, intervalMs]);
}
