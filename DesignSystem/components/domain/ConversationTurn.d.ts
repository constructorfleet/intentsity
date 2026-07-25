import * as React from 'react';
/**
 * A single turn in an intent-training conversation.
 * @startingPoint section="Domain" subtitle="User / assistant / tool turn" viewport="700x200"
 */
export interface ConversationTurnProps {
  role?: 'user'|'assistant'|'tool'|'system';
  name?: React.ReactNode; timestamp?: React.ReactNode;
  children?: React.ReactNode; editable?: boolean;
  onEdit?: () => void; actions?: React.ReactNode; style?: React.CSSProperties;
}
export declare function ConversationTurn(props: ConversationTurnProps): JSX.Element;
