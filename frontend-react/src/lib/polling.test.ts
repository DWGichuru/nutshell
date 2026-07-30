import { describe, expect, it } from 'vitest';
import { nextPollAction } from './polling';

describe('nextPollAction', () => {
  it('returns "done" when status is done', () => {
    expect(nextPollAction({ status: 'done' })).toBe('done');
  });

  it('returns "error" when status is error', () => {
    expect(nextPollAction({ status: 'error', error: 'boom' })).toBe('error');
  });

  it('returns "continue" for any in-progress status', () => {
    expect(nextPollAction({ status: 'pending' })).toBe('continue');
    expect(nextPollAction({ status: 'downloading' })).toBe('continue');
    expect(nextPollAction({ status: 'transcribing' })).toBe('continue');
    expect(nextPollAction({ status: 'summarizing' })).toBe('continue');
  });
});
