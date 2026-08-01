import { useState } from 'react';
import { Tabs, type TabDefinition } from '../../components/shared/Tabs';
import type { SummaryEntry, Transcript } from '../../api/types';

const TABS: TabDefinition[] = [
  { id: 'transcript', label: 'Transcript' },
  { id: 'summary', label: 'Summary' },
];

interface AiPaneProps {
  transcript: Transcript;
  summary: SummaryEntry | null;
}

export function AiPane({ transcript, summary }: AiPaneProps) {
  const [activeTab, setActiveTab] = useState('transcript');
  const [renderedTranscript, setRenderedTranscript] = useState(transcript);

  // Reset to the Transcript tab whenever a new transcript arrives, without an
  // effect (which would cause an extra render); see the React docs' "adjusting
  // state during render" pattern.
  if (transcript !== renderedTranscript) {
    setRenderedTranscript(transcript);
    setActiveTab('transcript');
  }

  const transcriptText = transcript.text.trim() === '' ? 'No speech detected in this clip.' : transcript.text;

  return (
    <Tabs tabs={TABS} activeId={activeTab} onChange={setActiveTab}>
      {activeTab === 'transcript' ? (
        <pre className="whitespace-pre-wrap text-sm">{transcriptText}</pre>
      ) : (
        <pre className="whitespace-pre-wrap text-sm">{summary?.content ?? ''}</pre>
      )}
    </Tabs>
  );
}
