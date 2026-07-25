import * as React from 'react';
export interface StatCellProps {
  label: React.ReactNode; value: React.ReactNode; unit?: React.ReactNode;
  delta?: React.ReactNode; deltaTone?: 'neutral'|'up'|'down';
  style?: React.CSSProperties;
}
export declare function StatCell(props: StatCellProps): JSX.Element;
