import * as React from 'react';
export interface SelectOption { value: string; label: string; }
export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>,'children'> {
  size?: 'sm'|'md'|'lg';
  invalid?: boolean;
  options: SelectOption[];
}
export declare function Select(props: SelectProps): JSX.Element;
