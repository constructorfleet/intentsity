import * as React from 'react';
export interface TagProps { children?: React.ReactNode; onRemove?: () => void; style?: React.CSSProperties; }
export declare function Tag(props: TagProps): JSX.Element;
