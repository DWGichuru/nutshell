export interface PollableStatus {
  status: string;
  error?: string | null;
}

export type PollAction = 'done' | 'error' | 'continue';

export function nextPollAction(response: PollableStatus): PollAction {
  if (response.status === 'done') return 'done';
  if (response.status === 'error') return 'error';
  return 'continue';
}
