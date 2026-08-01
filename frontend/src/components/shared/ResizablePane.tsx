import type { ReactNode } from 'react';
import { useResizablePane } from '../../hooks/useResizablePane';

const DIVIDER_RESTING_CLASSES =
  'bg-warm-gray/30 hover:bg-terracotta/50 dark:bg-warm-gray/20 dark:hover:bg-terracotta/50';
const DIVIDER_DRAGGING_CLASSES = 'bg-terracotta dark:bg-terracotta';

interface ResizablePaneProps {
  minWidth: number;
  minRemainder: number;
  defaultWidth?: number;
  paneContent: ReactNode;
  restContent: ReactNode;
}

export function ResizablePane({
  minWidth,
  minRemainder,
  defaultWidth = 420,
  paneContent,
  restContent,
}: ResizablePaneProps) {
  const { containerRef, paneRef, dividerRef, isDragging } = useResizablePane({ minWidth, minRemainder });

  return (
    <div ref={containerRef} className="flex flex-1 overflow-hidden">
      <div
        ref={paneRef}
        style={{ width: defaultWidth }}
        className="flex-shrink-0 space-y-6 overflow-y-auto p-8"
      >
        {paneContent}
      </div>
      <div
        ref={dividerRef}
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize panes"
        className={`w-1 flex-shrink-0 cursor-col-resize ${
          isDragging ? DIVIDER_DRAGGING_CLASSES : DIVIDER_RESTING_CLASSES
        }`}
      />
      <div className="flex-1 overflow-hidden">{restContent}</div>
    </div>
  );
}
