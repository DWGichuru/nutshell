import { useEffect, useRef, useState } from 'react';
import { clampWidth, computeMaxWidth } from '../lib/pane-math';

interface UseResizablePaneOptions {
  minWidth: number;
  minRemainder: number;
}

export function useResizablePane({ minWidth, minRemainder }: UseResizablePaneOptions) {
  const containerRef = useRef<HTMLDivElement>(null);
  const paneRef = useRef<HTMLDivElement>(null);
  const dividerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const dividerEl = dividerRef.current;
    const paneEl = paneRef.current;
    const containerEl = containerRef.current;
    if (!dividerEl || !paneEl || !containerEl) return;

    let startX = 0;
    let startWidth = 0;

    function onPointerMove(event: PointerEvent) {
      const rawWidth = startWidth + (event.clientX - startX);
      const maxWidth = computeMaxWidth(containerEl!.offsetWidth, minRemainder, dividerEl!.offsetWidth, minWidth);
      paneEl!.style.width = `${clampWidth(rawWidth, minWidth, maxWidth)}px`;
    }

    function onPointerUp() {
      setIsDragging(false);
      document.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('pointerup', onPointerUp);
    }

    function onPointerDown(event: PointerEvent) {
      startX = event.clientX;
      startWidth = paneEl!.offsetWidth;
      setIsDragging(true);
      document.addEventListener('pointermove', onPointerMove);
      document.addEventListener('pointerup', onPointerUp);
      event.preventDefault();
    }

    dividerEl.addEventListener('pointerdown', onPointerDown);
    return () => {
      dividerEl.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('pointerup', onPointerUp);
    };
  }, [minWidth, minRemainder]);

  return { containerRef, paneRef, dividerRef, isDragging };
}
