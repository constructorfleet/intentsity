import * as React from 'react';
export interface ToolInvocationProps {
  name: string; args: any; result?: any;
  status?: 'ok'|'pending'|'error';
  editable?: boolean; onEditArgs?: () => void;
  style?: React.CSSProperties;
}
export declare function ToolInvocation(props: ToolInvocationProps): JSX.Element;
