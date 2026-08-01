import { useEffect, useState } from 'react';
import { ResizablePane } from '../../components/shared/ResizablePane';
import { AsyncStatus } from '../../components/shared/AsyncStatus';
import { SearchSection } from './SearchSection';
import { LibraryAiPane } from './LibraryAiPane';
import { GenerateSummarySection } from './GenerateSummarySection';
import { getVideo, getTranscript, getSummaries } from '../../api/client';
import type { SummaryEntry, VideoMeta } from '../../api/types';

const RESIZABLE_PANE_BOUNDS = { minWidth: 280, minRemainder: 320 };

interface VideoDetail {
  videoId: string;
  video: VideoMeta;
  transcriptText: string;
}

interface DetailError {
  videoId: string;
  message: string;
}

interface SummariesState {
  videoId: string;
  entries: SummaryEntry[];
}

interface SummariesError {
  videoId: string;
  message: string;
}

export function LibraryPage() {
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [detailError, setDetailError] = useState<DetailError | null>(null);
  const [summaries, setSummaries] = useState<SummariesState | null>(null);
  const [summariesError, setSummariesError] = useState<SummariesError | null>(null);

  function refreshSummaries(videoId: string) {
    getSummaries(videoId)
      .then((result) => {
        setSummaries({ videoId, entries: result.summaries });
        setSummariesError(null);
      })
      .catch((err) => {
        setSummariesError({ videoId, message: err instanceof Error ? err.message : 'Unable to load summaries.' });
      });
  }

  useEffect(() => {
    if (selectedVideoId === null) return;
    let active = true;

    getVideo(selectedVideoId)
      .then((video) =>
        getTranscript(selectedVideoId)
          .then((transcript) =>
            transcript.text.trim() === '' ? 'No speech detected in this clip.' : transcript.text,
          )
          .catch(() => 'No transcript yet for this video.')
          .then((transcriptText) => {
            if (!active) return;
            setDetail({ videoId: selectedVideoId, video, transcriptText });
            refreshSummaries(selectedVideoId);
          }),
      )
      .catch((err) => {
        if (!active) return;
        setDetailError({
          videoId: selectedVideoId,
          message: err instanceof Error ? err.message : 'Unable to load video.',
        });
      });

    return () => {
      active = false;
    };
  }, [selectedVideoId]);

  const isCurrent = detail !== null && detail.videoId === selectedVideoId;
  const currentError = detailError !== null && detailError.videoId === selectedVideoId ? detailError.message : null;
  const currentSummaries =
    summaries !== null && summaries.videoId === selectedVideoId ? summaries.entries : null;
  const currentSummariesError =
    summariesError !== null && summariesError.videoId === selectedVideoId ? summariesError.message : null;

  return (
    <main className="flex h-full">
      <ResizablePane
        {...RESIZABLE_PANE_BOUNDS}
        paneContent={
          <>
            <SearchSection selectedVideoId={selectedVideoId} onSelectVideo={setSelectedVideoId} />
            {isCurrent && (
              <GenerateSummarySection
                key={detail.videoId}
                videoId={detail.videoId}
                onSummarized={() => refreshSummaries(detail.videoId)}
              />
            )}
          </>
        }
        restContent={
          isCurrent ? (
            <LibraryAiPane
              key={detail.videoId}
              video={detail.video}
              transcriptText={detail.transcriptText}
              summaries={currentSummaries}
              summariesError={currentSummariesError}
            />
          ) : (
            <div className="flex h-full items-center justify-center p-10 text-center text-warm-gray">
              {selectedVideoId === null ? (
                <p>Select a video from the library to view its transcript and summaries.</p>
              ) : (
                <div>
                  {currentError === null && <p>Loading video...</p>}
                  <AsyncStatus busy={currentError === null} statusText={null} error={currentError} />
                </div>
              )}
            </div>
          )
        }
      />
    </main>
  );
}
