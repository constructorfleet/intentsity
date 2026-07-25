import * as React from 'react';
export type BadgeTone = 'neutral'|'brand'|'tp'|'tn'|'fp'|'fn'|'bgnoise';
export interface BadgeProps {
  tone?: BadgeTone; children?: React.ReactNode; mono?: boolean; dot?: boolean;
  style?: React.CSSProperties;
}
export declare function Badge(props: BadgeProps): JSX.Element;
