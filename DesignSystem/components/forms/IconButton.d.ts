import * as React from 'react';
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: 'sm'|'md'|'lg';
  variant?: 'ghost'|'primary'|'outline';
  active?: boolean;
  'aria-label': string;
  children?: React.ReactNode;
}
export declare function IconButton(props: IconButtonProps): JSX.Element;
