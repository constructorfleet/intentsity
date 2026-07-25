import * as React from 'react';
/**
 * Audio-clip waveform visualization. Static bars unless `onScrub` is provided.
 * @startingPoint section="Domain" subtitle="Waveform preview" viewport="700x120"
 */
export interface WaveformProps {
  bars?: number[]; samples?: number; seed?: number;
  playhead?: number; color?: string; height?: number;
  barWidth?: number; barGap?: number;
  region?: { start: number; end: number };
  onScrub?: (position: number) => void;
  style?: React.CSSProperties;
}
export declare function Waveform(props: WaveformProps): JSX.Element;
