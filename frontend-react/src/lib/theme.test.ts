import { describe, expect, it } from 'vitest';
import { resolveInitialTheme } from './theme';

describe('resolveInitialTheme', () => {
  it('uses the stored value when it is a valid theme', () => {
    expect(resolveInitialTheme('dark', false)).toBe('dark');
    expect(resolveInitialTheme('light', true)).toBe('light');
  });

  it('falls back to the OS preference when nothing valid is stored', () => {
    expect(resolveInitialTheme(null, true)).toBe('dark');
    expect(resolveInitialTheme(null, false)).toBe('light');
  });

  it('falls back to the OS preference when the stored value is invalid', () => {
    expect(resolveInitialTheme('system', true)).toBe('dark');
    expect(resolveInitialTheme('', false)).toBe('light');
  });
});
