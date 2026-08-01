export function computeMaxWidth(
  containerWidth: number,
  minRemainder: number,
  dividerWidth: number,
  minWidth: number,
): number {
  return Math.max(minWidth, containerWidth - minRemainder - dividerWidth);
}

export function clampWidth(rawWidth: number, minWidth: number, maxWidth: number): number {
  return Math.min(Math.max(rawWidth, minWidth), maxWidth);
}
