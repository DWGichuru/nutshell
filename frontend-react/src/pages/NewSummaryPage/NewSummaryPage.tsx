import { useState } from 'react';
import { ResizablePane } from '../../components/shared/ResizablePane';
import { DownloadSection } from './DownloadSection';
import { TrimSection } from './TrimSection';
import { TranscribeSection } from './TranscribeSection';
import { SummarizeSection } from './SummarizeSection';
import { AiPane } from './AiPane';
import type { SummaryEntry, Transcript } from '../../api/types';

const RESIZABLE_PANE_BOUNDS = { minWidth: 280, minRemainder: 320 };

export function NewSummaryPage() {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [isDownloaded, setIsDownloaded] = useState(false);
  const [isTrimmed, setIsTrimmed] = useState(false);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [latestSummary, setLatestSummary] = useState<SummaryEntry | null>(null);

  function handleDownloadStarted(newVideoId: string) {
    setVideoId(newVideoId);
    setIsDownloaded(false);
    setIsTrimmed(false);
    setTranscript(null);
    setLatestSummary(null);
  }

  function handleDownloadComplete() {
    setIsDownloaded(true);
  }

  function handleTrimmed() {
    setIsTrimmed(true);
  }

  function handleTranscribed(newTranscript: Transcript) {
    setTranscript(newTranscript);
    setLatestSummary(null);
  }

  function handleSummarized(summary: SummaryEntry) {
    setLatestSummary(summary);
  }

  const hasTranscriptText = transcript !== null && transcript.text.trim() !== '';

  return (
    <main className="flex h-full">
      <ResizablePane
        {...RESIZABLE_PANE_BOUNDS}
        paneContent={
          <>
            <DownloadSection
              onDownloadStarted={handleDownloadStarted}
              onDownloadComplete={handleDownloadComplete}
            />
            {isDownloaded && videoId && <TrimSection videoId={videoId} onTrimmed={handleTrimmed} />}
            {isTrimmed && videoId && (
              <TranscribeSection videoId={videoId} onTranscribed={handleTranscribed} />
            )}
            {hasTranscriptText && videoId && (
              <SummarizeSection videoId={videoId} onSummarized={handleSummarized} />
            )}
          </>
        }
        restContent={
          transcript ? (
            <AiPane transcript={transcript} summary={latestSummary} />
          ) : (
            <div className="flex h-full items-center justify-center p-10 text-center text-warm-gray">
              <p>Paste a link and download to see the transcript and summary here.</p>
            </div>
          )
        }
      />
    </main>
  );
}
