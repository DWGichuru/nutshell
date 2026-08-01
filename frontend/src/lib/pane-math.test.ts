import { describe, expect, it } from 'vitest';
import { clampWidth, computeMaxWidth } from './pane-math';

describe('computeMaxWidth', () => {
  it('computes the remaining width after minRemainder and divider', () => {
    expect(computeMaxWidth(1000, 320, 8, 280)).toBe(672);
  });

  it('falls back to minWidth when the container is too small', () => {
    expect(computeMaxWidth(400, 320, 8, 280)).toBe(280);
  });
});

describe('clampWidth', () => {
  it('clamps a raw width below minWidth up to minWidth', () => {
    expect(clampWidth(100, 280, 672)).toBe(280);
  });

  it('clamps a raw width above maxWidth down to maxWidth', () => {
    expect(clampWidth(900, 280, 672)).toBe(672);
  });

  it('passes through a raw width already within bounds', () => {
    expect(clampWidth(400, 280, 672)).toBe(400);
  });
});
