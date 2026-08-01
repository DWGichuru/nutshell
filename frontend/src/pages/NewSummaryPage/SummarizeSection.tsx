import { useState } from 'react';
import { startSummarization, getSummarizationStatus, getSummaries } from '../../api/client';
import type { SummarizationProvider, SummarizationStatusResponse, SummaryEntry } from '../../api/types';
import { usePolling } from '../../hooks/usePolling';
import { AsyncStatus } from '../../components/shared/AsyncStatus';

interface SummarizeSectionProps {
  videoId: string;
  onSummarized: (summary: SummaryEntry) => void;
}

export function SummarizeSection({ videoId, onSummarized }: SummarizeSectionProps) {
  const [provider, setProvider] = useState<SummarizationProvider>('anthropic');
  const [summarizing, setSummarizing] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingVideoId, setPollingVideoId] = useState<string | null>(null);

  usePolling<SummarizationStatusResponse>({
    key: pollingVideoId,
    fetchStatus: async (id) => {
      const status = await getSummarizationStatus(id);
      setStatusText(`Status: ${status.status}...`);
      return status;
    },
    onDone: async () => {
      setStatusText('Summary complete.');
      try {
        const { summaries } = await getSummaries(videoId);
        const latest = summaries[0];
        if (latest) onSummarized(latest);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load summary.');
      } finally {
        setSummarizing(false);
      }
    },
    onError: (status) => {
      setSummarizing(false);
      setStatusText(null);
      setError(status.error || 'Summarization failed.');
    },
  });

  async function handleSummarize() {
    setError(null);
    setSummarizing(true);
    setStatusText('Starting summarization...');

    try {
      await startSummarization(videoId, provider);
      setPollingVideoId(videoId);
    } catch (err) {
      setSummarizing(false);
      setStatusText(null);
      setError(err instanceof Error ? err.message : 'Summarization request failed.');
    }
  }

  return (
    <section className="rounded-lg bg-ivory p-6 dark:bg-near-black dark:border dark:border-warm-gray/30">
      <h2 className="mb-4 text-lg font-semibold tracking-tight">Summarize</h2>
      <fieldset className="mb-4 flex items-center gap-6">
        <legend className="sr-only">Summary provider</legend>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="summary-provider"
            value="anthropic"
            checked={provider === 'anthropic'}
            onChange={() => setProvider('anthropic')}
          />
          Anthropic (Claude)
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="summary-provider"
            value="openai"
            checked={provider === 'openai'}
            onChange={() => setProvider('openai')}
          />
          OpenAI
        </label>
      </fieldset>
      <button
        type="button"
        onClick={handleSummarize}
        disabled={summarizing}
        className="mt-4 rounded bg-terracotta px-4 py-2 text-sm font-medium text-cream hover:bg-terracotta-dark disabled:opacity-50"
      >
        Summarize
      </button>
      <AsyncStatus busy={summarizing} statusText={statusText} error={error} />
    </section>
  );
}
