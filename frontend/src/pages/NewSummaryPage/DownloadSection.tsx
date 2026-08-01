import { useState } from 'react';
import { previewMetadata, startDownload, getDownloadStatus } from '../../api/client';
import type { DownloadStatusResponse, VideoMetadataResponse } from '../../api/types';
import { usePolling } from '../../hooks/usePolling';
import { AsyncStatus } from '../../components/shared/AsyncStatus';
import { formatTime } from '../../lib/format';

interface DownloadSectionProps {
  onDownloadStarted: (videoId: string) => void;
  onDownloadComplete: () => void;
}

export function DownloadSection({ onDownloadStarted, onDownloadComplete }: DownloadSectionProps) {
  const [url, setUrl] = useState('');
  const [metadata, setMetadata] = useState<VideoMetadataResponse | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingVideoId, setPollingVideoId] = useState<string | null>(null);

  usePolling<DownloadStatusResponse>({
    key: pollingVideoId,
    fetchStatus: async (videoId) => {
      const status = await getDownloadStatus(videoId);
      setStatusText(`Status: ${status.status}...`);
      return status;
    },
    onDone: () => {
      setDownloading(false);
      setStatusText('Download complete.');
      onDownloadComplete();
    },
    onError: (status) => {
      setDownloading(false);
      setStatusText(null);
      setError(status.error || 'Download failed.');
    },
  });

  async function handlePreview() {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setError('Enter a YouTube URL first.');
      return;
    }

    setError(null);
    setMetadata(null);
    setPreviewing(true);
    try {
      const result = await previewMetadata(trimmedUrl);
      setMetadata(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to fetch video metadata.');
    } finally {
      setPreviewing(false);
    }
  }

  async function handleDownload() {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;

    setError(null);
    setDownloading(true);
    setStatusText('Starting download...');

    try {
      const response = await startDownload(trimmedUrl);
      onDownloadStarted(response.video_id);
      setPollingVideoId(response.video_id);
    } catch (err) {
      setDownloading(false);
      setStatusText(null);
      setError(err instanceof Error ? err.message : 'Download request failed.');
    }
  }

  const busy = previewing || downloading;

  return (
    <section className="rounded-lg bg-ivory p-6 dark:bg-near-black dark:border dark:border-warm-gray/30">
      <h2 className="mb-4 font-serif text-xl font-semibold">New Summary</h2>
      <label htmlFor="video-url" className="mb-2 block font-medium">
        YouTube URL
      </label>
      <div className="flex gap-3">
        <input
          id="video-url"
          type="text"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          className="flex-1 rounded border border-warm-gray/40 bg-cream px-3 py-2 text-espresso focus:outline-none focus:ring-2 focus:ring-terracotta dark:bg-near-black dark:text-cream"
        />
        <button
          type="button"
          onClick={handlePreview}
          disabled={busy}
          className="rounded bg-terracotta px-4 py-2 font-medium text-cream hover:bg-terracotta-dark disabled:opacity-50"
        >
          Preview
        </button>
      </div>

      {metadata && (
        <div className="mt-4 rounded bg-cream p-4 text-sm dark:bg-espresso/40">
          <p className="font-medium">{metadata.title}</p>
          <p className="text-warm-gray">
            {metadata.channel} - {formatTime(metadata.duration_seconds)}
          </p>
          {metadata.needs_confirmation && (
            <p className="mt-2 text-rust">
              This video is long - estimated transcription time is about{' '}
              {metadata.estimated_minutes} minute{metadata.estimated_minutes === 1 ? '' : 's'}.
            </p>
          )}
          <button
            type="button"
            onClick={handleDownload}
            disabled={busy}
            className="mt-3 rounded bg-terracotta px-4 py-2 font-medium text-cream hover:bg-terracotta-dark disabled:opacity-50"
          >
            {metadata.needs_confirmation ? 'Confirm & Download' : 'Download'}
          </button>
        </div>
      )}

      <AsyncStatus busy={busy} statusText={statusText} error={error} />
    </section>
  );
}
