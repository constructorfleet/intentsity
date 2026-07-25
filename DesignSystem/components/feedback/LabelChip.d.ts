import * as React from 'react';
/**
 * The five wake-word annotation labels as selectable chips.
 * @startingPoint section="Domain" subtitle="Annotation label picker" viewport="700x120"
 */
export type LabelTone = 'tp'|'tn'|'fp'|'fn'|'bgnoise';
export interface LabelChipProps {
  tone: LabelTone; selected?: boolean; onClick?: () => void;
  shortcut?: string; children?: React.ReactNode; style?: React.CSSProperties;
}
export declare function LabelChip(props: LabelChipProps): JSX.Element;
export declare const WAKE_LABELS: Array<{id:string;label:string;short:string;tone:LabelTone;key:string}>;
