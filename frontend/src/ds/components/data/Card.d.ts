import * as React from 'react';
export interface CardProps {
  title?: React.ReactNode; actions?: React.ReactNode; footer?: React.ReactNode;
  children?: React.ReactNode; style?: React.CSSProperties; padded?: boolean;
  elevation?: 'flat'|'raised'|'floating';
}
export declare function Card(props: CardProps): JSX.Element;
