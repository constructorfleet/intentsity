import * as React from 'react';
export interface KVItem { k: React.ReactNode; v: React.ReactNode; mono?: boolean; }
export interface KeyValueProps { items: KVItem[]; layout?: 'rows'|'columns'; style?: React.CSSProperties; }
export declare function KeyValue(props: KeyValueProps): JSX.Element;
