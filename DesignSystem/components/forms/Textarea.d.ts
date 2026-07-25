import * as React from 'react';
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  invalid?: boolean; minRows?: number;
}
export declare function Textarea(props: TextareaProps): JSX.Element;
