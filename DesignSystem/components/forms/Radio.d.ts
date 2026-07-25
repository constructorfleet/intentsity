import * as React from 'react';
export interface RadioProps {
  checked?: boolean; onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label?: React.ReactNode; name?: string; value?: string; disabled?: boolean; id?: string;
  style?: React.CSSProperties;
}
export declare function Radio(props: RadioProps): JSX.Element;
export interface RadioGroupProps { children?: React.ReactNode; style?: React.CSSProperties; }
export declare function RadioGroup(props: RadioGroupProps): JSX.Element;
