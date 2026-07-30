import { useState } from 'react';
import { startTranscription, getTranscriptionStatus, getTranscript } from '../../api/client';
import type { Transcript, TranscriptionMethod, TranscriptionStatusResponse } from '../../api/types';
import { usePolling } from '../../hooks/usePolling';
import { AsyncStatus } from '../../components/shared/AsyncStatus';

interface TranscribeSectionProps {
  videoId: string;
  onTranscribed: (transcript: Transcript) => void;
}

export function TranscribeSection({ videoId, onTranscribed }: TranscribeSectionProps) {
  const [method, setMethod] = useState<TranscriptionMethod>('api');
  const [transcribing, setTranscribing] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingVideoId, setPollingVideoId] = useState<string | null>(null);

  usePolling<TranscriptionStatusResponse>({
    key: pollingVideoId,
    fetchStatus: async (id) => {
      const status = await getTranscriptionStatus(id);
      setStatusText(`Status: ${status.status}...`);
      return status;
    },
    onDone: async () => {
      setStatusText('Transcription complete.');
      try {
        const transcript = await getTranscript(videoId);
        onTranscribed(transcript);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load transcript.');
      } finally {
        setTranscribing(false);
      }
    },
    onError: (status) => {
      setTranscribing(false);
      setStatusText(null);
      setError(status.error || 'Transcription failed.');
    },
  });

  async function handleTranscribe() {
    setError(null);
    setTranscribing(true);
    setStatusText('Starting transcription...');

    try {
      await startTranscription(videoId, method);
      setPollingVideoId(videoId);
    } catch (err) {
      setTranscribing(false);
      setStatusText(null);
      setError(err instanceof Error ? err.message : 'Transcription request failed.');
    }
  }

  return (
    <section className="rounded-lg bg-ivory p-6 dark:bg-near-black dark:border dark:border-warm-gray/30">
      <h2 className="mb-4 font-serif text-xl font-semibold">Transcribe</h2>
      <fieldset className="flex items-center gap-6">
        <legend className="sr-only">Transcription method</legend>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="transcription-method"
            value="api"
            checked={method === 'api'}
            onChange={() => setMethod('api')}
          />
          API (OpenAI Whisper) - costs per minute of audio
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="transcription-method"
            value="local"
            checked={method === 'local'}
            onChange={() => setMethod('local')}
          />
          Local (mlx-whisper) - free, on-device, first run downloads the model
        </label>
      </fieldset>
      <button
        type="button"
        onClick={handleTranscribe}
        disabled={transcribing}
        className="mt-4 rounded bg-terracotta px-4 py-2 font-medium text-cream hover:bg-terracotta-dark disabled:opacity-50"
      >
        Transcribe
      </button>
      <AsyncStatus busy={transcribing} statusText={statusText} error={error} />
    </section>
  );
}
