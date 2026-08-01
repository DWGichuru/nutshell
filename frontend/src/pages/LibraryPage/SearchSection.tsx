import { useEffect, useState } from 'react';
import { listVideos } from '../../api/client';
import type { VideoSummary } from '../../api/types';
import { AsyncStatus } from '../../components/shared/AsyncStatus';
import { formatDate } from '../../lib/format';

const SELECTED_ROW_CLASSES = 'rounded pl-2 bg-terracotta/10 border-l-2 border-terracotta';

interface SearchSectionProps {
  selectedVideoId: string | null;
  onSelectVideo: (videoId: string) => void;
}

export function SearchSection({ selectedVideoId, onSelectVideo }: SearchSectionProps) {
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [videos, setVideos] = useState<VideoSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchVideos() {
    setError(null);
    setLoading(true);
    try {
      const result = await listVideos({
        search: search.trim() || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setVideos(result.videos);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load videos.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Deferred so fetchVideos' setState calls don't run synchronously within
    // the effect body; only run once on mount, so fetchVideos is deliberately
    // excluded from the dependency array.
    Promise.resolve().then(() => fetchVideos());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFilterKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'Enter') fetchVideos();
  }

  return (
    <section className="rounded-lg bg-ivory p-6 dark:bg-near-black dark:border dark:border-warm-gray/30">
      <h2 className="mb-4 text-lg font-semibold tracking-tight">Library</h2>

      <label htmlFor="library-search" className="mb-1 block text-sm font-medium">
        Search (title or channel)
      </label>
      <input
        id="library-search"
        type="text"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        onKeyDown={handleFilterKeyDown}
        className="mb-3 w-full rounded border border-warm-gray/40 bg-cream px-3 py-2 text-sm text-espresso focus:outline-none focus:ring-2 focus:ring-terracotta dark:bg-near-black dark:text-cream"
      />

      <div className="mb-3 flex gap-3">
        <div className="flex-1">
          <label htmlFor="library-date-from" className="mb-1 block text-sm font-medium">
            From
          </label>
          <input
            id="library-date-from"
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
            onKeyDown={handleFilterKeyDown}
            className="w-full rounded border border-warm-gray/40 bg-cream px-3 py-2 text-sm text-espresso focus:outline-none focus:ring-2 focus:ring-terracotta dark:bg-near-black dark:text-cream"
          />
        </div>
        <div className="flex-1">
          <label htmlFor="library-date-to" className="mb-1 block text-sm font-medium">
            To
          </label>
          <input
            id="library-date-to"
            type="date"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
            onKeyDown={handleFilterKeyDown}
            className="w-full rounded border border-warm-gray/40 bg-cream px-3 py-2 text-sm text-espresso focus:outline-none focus:ring-2 focus:ring-terracotta dark:bg-near-black dark:text-cream"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={fetchVideos}
        disabled={loading}
        className="rounded bg-terracotta px-4 py-2 text-sm font-medium text-cream hover:bg-terracotta-dark disabled:opacity-50"
      >
        Filter
      </button>

      <AsyncStatus busy={loading} statusText={null} error={error} />

      <ul className="mt-4 divide-y divide-warm-gray/20">
        {videos.length === 0 && !loading ? (
          <li className="py-3 text-sm text-warm-gray">No videos found.</li>
        ) : (
          videos.map((video) => (
            <li
              key={video.video_id}
              className={`py-3 ${video.video_id === selectedVideoId ? SELECTED_ROW_CLASSES : ''}`}
            >
              <button
                type="button"
                onClick={() => onSelectVideo(video.video_id)}
                className="w-full text-left hover:text-terracotta"
              >
                <span className="text-sm font-medium">{video.title}</span>
                <span className="block text-xs text-warm-gray">
                  {video.channel} - {formatDate(video.date_added)}
                </span>
              </button>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
