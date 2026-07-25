import * as React from 'react';
export interface TabItem { value: string; label: React.ReactNode; count?: number; }
export interface TabsProps { tabs: TabItem[]; value?: string; onChange?: (v: string) => void; size?: 'md'|'sm'; style?: React.CSSProperties; }
export declare function Tabs(props: TabsProps): JSX.Element;
