import { useRef, useState } from 'react';
import { trimAudio } from '../../api/client';
import { useWaveform } from '../../hooks/useWaveform';
import { AsyncStatus } from '../../components/shared/AsyncStatus';
import { formatTime } from '../../lib/format';

interface TrimSectionProps {
  videoId: string;
  onTrimmed: () => void;
}

export function TrimSection({ videoId, onTrimmed }: TrimSectionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [trimming, setTrimming] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { trimStart, trimEnd, isPlaying, togglePlayPause, skipBack, skipForward, previewSelection, getActiveRegion } =
    useWaveform({ containerRef, videoId, reloadKey });

  async function handleTrim() {
    const region = getActiveRegion();
    if (!region) return;

    setError(null);
    setTrimming(true);
    setStatusText('Trimming...');

    try {
      await trimAudio(videoId, region.start, region.end);
      setStatusText('Trim complete.');
      setReloadKey((key) => key + 1);
      onTrimmed();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trim request failed.');
      setStatusText(null);
    } finally {
      setTrimming(false);
    }
  }

  return (
    <section className="rounded-lg bg-ivory p-6 dark:bg-near-black dark:border dark:border-warm-gray/30">
      <h2 className="mb-4 font-serif text-xl font-semibold">Trim</h2>
      <div id="waveform" ref={containerRef} className="rounded bg-cream dark:bg-espresso/40" />
      <div className="mt-4 flex items-center gap-2">
        <button
          type="button"
          onClick={skipBack}
          aria-label="Skip back 5 seconds"
          className="rounded bg-ivory px-3 py-1.5 font-medium text-espresso hover:bg-warm-gray/30 dark:bg-espresso/60 dark:text-cream"
        >
          «5
        </button>
        <button
          type="button"
          onClick={togglePlayPause}
          aria-label={isPlaying ? 'Pause' : 'Play'}
          className="rounded bg-terracotta px-3 py-1.5 font-medium text-cream hover:bg-terracotta-dark"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          onClick={skipForward}
          aria-label="Skip forward 5 seconds"
          className="rounded bg-ivory px-3 py-1.5 font-medium text-espresso hover:bg-warm-gray/30 dark:bg-espresso/60 dark:text-cream"
        >
          5»
        </button>
      </div>
      <div className="mt-4 flex items-center gap-4 text-sm">
        <span>
          Start: <span className="font-medium text-terracotta">{formatTime(trimStart)}</span>
        </span>
        <span>
          End: <span className="font-medium text-terracotta">{formatTime(trimEnd)}</span>
        </span>
        <button
          type="button"
          onClick={previewSelection}
          className="ml-auto rounded bg-terracotta px-3 py-1.5 font-medium text-cream hover:bg-terracotta-dark"
        >
          Preview
        </button>
        <button
          type="button"
          onClick={handleTrim}
          disabled={trimming}
          className="rounded bg-sage px-3 py-1.5 font-medium text-cream hover:opacity-90 disabled:opacity-50"
        >
          Trim
        </button>
      </div>
      <AsyncStatus busy={trimming} statusText={statusText} error={error} />
    </section>
  );
}
