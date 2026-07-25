import * as React from 'react';
export interface SidebarProps { children?: React.ReactNode; width?: number; style?: React.CSSProperties; }
export declare function Sidebar(props: SidebarProps): JSX.Element;
export interface SidebarSectionProps { title?: React.ReactNode; children?: React.ReactNode; style?: React.CSSProperties; }
export declare function SidebarSection(props: SidebarSectionProps): JSX.Element;
export interface SidebarItemProps {
  icon?: React.ReactNode; active?: boolean; badge?: React.ReactNode;
  children?: React.ReactNode; onClick?: () => void; style?: React.CSSProperties;
}
export declare function SidebarItem(props: SidebarItemProps): JSX.Element;
