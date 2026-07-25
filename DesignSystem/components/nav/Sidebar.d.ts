import * as React from 'react';
export interface SidebarProps {
  children?: React.ReactNode; width?: number;
  collapsed?: boolean; collapsedWidth?: number; style?: React.CSSProperties;
}
export declare function Sidebar(props: SidebarProps): JSX.Element;
/** True when the enclosing Sidebar is collapsed to its icon rail. */
export declare function useSidebarCollapsed(): boolean;
export interface SidebarSectionProps { title?: React.ReactNode; children?: React.ReactNode; style?: React.CSSProperties; }
export declare function SidebarSection(props: SidebarSectionProps): JSX.Element;
export interface SidebarItemProps {
  icon?: React.ReactNode; active?: boolean; badge?: React.ReactNode;
  children?: React.ReactNode; onClick?: () => void;
  /** Native tooltip; defaults to the label text while collapsed. */
  title?: string;
  style?: React.CSSProperties;
}
export declare function SidebarItem(props: SidebarItemProps): JSX.Element;
