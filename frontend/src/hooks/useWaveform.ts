import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin, { type Region } from 'wavesurfer.js/plugins/regions';
import { audioUrl } from '../api/client';

const SKIP_SECONDS = 5;

interface UseWaveformOptions {
  containerRef: React.RefObject<HTMLDivElement | null>;
  videoId: string | null;
  reloadKey: number;
}

export function useWaveform({ containerRef, videoId, reloadKey }: UseWaveformOptions) {
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const activeRegionRef = useRef<Region | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);

  useEffect(() => {
    if (!videoId || !containerRef.current) return;

    const regions = RegionsPlugin.create();
    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#8A7A6A',
      progressColor: '#C96F45',
      cursorColor: '#3A2A1E',
      height: 96,
      url: `${audioUrl(videoId)}?t=${Date.now()}`,
      plugins: [regions],
    });
    wavesurferRef.current = wavesurfer;

    wavesurfer.on('decode', (duration) => {
      const region = regions.addRegion({
        start: 0,
        end: duration,
        color: 'rgba(201, 111, 69, 0.2)',
        drag: true,
        resize: true,
      });
      activeRegionRef.current = region;
      setTrimStart(region.start);
      setTrimEnd(region.end);
    });

    regions.on('region-updated', (region) => {
      activeRegionRef.current = region;
      setTrimStart(region.start);
      setTrimEnd(region.end);
    });

    wavesurfer.on('play', () => setIsPlaying(true));
    wavesurfer.on('pause', () => setIsPlaying(false));
    wavesurfer.on('finish', () => setIsPlaying(false));
    setIsPlaying(false);

    return () => {
      wavesurfer.destroy();
      wavesurferRef.current = null;
      activeRegionRef.current = null;
    };
  }, [videoId, reloadKey, containerRef]);

  function togglePlayPause() {
    wavesurferRef.current?.playPause();
  }

  function skipBack() {
    wavesurferRef.current?.skip(-SKIP_SECONDS);
  }

  function skipForward() {
    wavesurferRef.current?.skip(SKIP_SECONDS);
  }

  function previewSelection() {
    const region = activeRegionRef.current;
    if (!wavesurferRef.current || !region) return;
    wavesurferRef.current.play(region.start, region.end);
  }

  function getActiveRegion() {
    return activeRegionRef.current;
  }

  return {
    isPlaying,
    trimStart,
    trimEnd,
    togglePlayPause,
    skipBack,
    skipForward,
    previewSelection,
    getActiveRegion,
  };
}
