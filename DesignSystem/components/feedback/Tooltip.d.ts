import * as React from 'react';
export interface TooltipProps { content: React.ReactNode; placement?: 'top'|'bottom'|'left'|'right'; delay?: number; children: React.ReactNode; }
export declare function Tooltip(props: TooltipProps): JSX.Element;
