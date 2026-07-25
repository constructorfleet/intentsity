import * as React from 'react';
export interface ToastProps {
  tone?: 'info'|'success'|'warn'|'error';
  title?: React.ReactNode; description?: React.ReactNode;
  onDismiss?: () => void; style?: React.CSSProperties;
}
export declare function Toast(props: ToastProps): JSX.Element;
