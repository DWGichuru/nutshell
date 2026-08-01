import { useState } from 'react';
import { Tabs, type TabDefinition } from '../../components/shared/Tabs';
import type { SummaryEntry, VideoMeta } from '../../api/types';
import { AsyncStatus } from '../../components/shared/AsyncStatus';
import { formatDate } from '../../lib/format';

const TABS: TabDefinition[] = [
  { id: 'transcript', label: 'Transcript' },
  { id: 'summary', label: 'Summary' },
];

interface LibraryAiPaneProps {
  video: VideoMeta;
  transcriptText: string;
  summaries: SummaryEntry[] | null;
  summariesError: string | null;
}

export function LibraryAiPane({ video, transcriptText, summaries, summariesError }: LibraryAiPaneProps) {
  const [activeTab, setActiveTab] = useState('transcript');

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="bg-ivory px-8 pt-6 dark:bg-espresso/60">
        <h2 className="mb-1 text-xl font-semibold tracking-tight">{video.title}</h2>
        <p className="mb-4 text-xs text-warm-gray">
          {video.channel} - {formatDate(video.date_added)}
        </p>
      </div>
      <Tabs tabs={TABS} activeId={activeTab} onChange={setActiveTab}>
        {activeTab === 'transcript' ? (
          <pre className="whitespace-pre-wrap text-sm">{transcriptText}</pre>
        ) : (
          <SummaryHistory summaries={summaries} error={summariesError} />
        )}
      </Tabs>
    </div>
  );
}

function SummaryHistory({ summaries, error }: { summaries: SummaryEntry[] | null; error: string | null }) {
  if (error) {
    return <AsyncStatus busy={false} statusText={null} error={error} />;
  }
  if (summaries === null) {
    return <p className="text-sm text-warm-gray">Loading summaries...</p>;
  }
  if (summaries.length === 0) {
    return <p className="text-sm text-warm-gray">No summaries yet.</p>;
  }

  return (
    <div className="space-y-3">
      {summaries.map((summary) => (
        <div key={summary.created_at} className="rounded bg-cream p-4 dark:bg-espresso/40">
          <p className="mb-2 text-xs font-medium text-terracotta">{summary.created_at}</p>
          <pre className="whitespace-pre-wrap text-sm">{summary.content}</pre>
        </div>
      ))}
    </div>
  );
}
