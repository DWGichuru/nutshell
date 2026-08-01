import { describe, expect, it } from 'vitest';
import { formatDate, formatTime } from './format';

describe('formatTime', () => {
  it('formats zero seconds', () => {
    expect(formatTime(0)).toBe('0:00');
  });

  it('pads seconds under 10', () => {
    expect(formatTime(65)).toBe('1:05');
  });

  it('rounds fractional seconds', () => {
    expect(formatTime(59.6)).toBe('1:00');
  });

  it('clamps negative input to zero', () => {
    expect(formatTime(-5)).toBe('0:00');
  });

  it('formats durations over an hour as raw minutes', () => {
    expect(formatTime(3661)).toBe('61:01');
  });
});

describe('formatDate', () => {
  it('formats a valid ISO date string', () => {
    const result = formatDate('2024-01-15T10:00:00.000Z');
    expect(result).toBe(new Date('2024-01-15T10:00:00.000Z').toLocaleDateString());
  });

  it('returns the original string when malformed', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date');
  });

  it('returns the original string when empty', () => {
    expect(formatDate('')).toBe('');
  });
});
