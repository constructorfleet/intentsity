import React from 'react';

const sizes = {
  sm: { h: 28, px: 10, fs: 13, gap: 6, r: 'var(--r-md)' },
  md: { h: 34, px: 14, fs: 14, gap: 8, r: 'var(--r-md)' },
  lg: { h: 42, px: 18, fs: 15, gap: 10, r: 'var(--r-lg)' },
};

const variants = {
  primary: {
    background: 'var(--accent)', color: 'var(--text-on-brand)', border: '1px solid transparent',
    hoverBg: 'var(--accent-hover)', activeBg: 'var(--accent-active)',
  },
  secondary: {
    background: 'var(--surface-panel)', color: 'var(--text-body)', border: '1px solid var(--border-default)',
    hoverBg: 'var(--surface-hover)', activeBg: 'var(--surface-active)',
  },
  ghost: {
    background: 'transparent', color: 'var(--text-body)', border: '1px solid transparent',
    hoverBg: 'var(--surface-hover)', activeBg: 'var(--surface-active)',
  },
  danger: {
    background: 'var(--fp-500)', color: '#fff', border: '1px solid transparent',
    hoverBg: 'var(--fp-600)', activeBg: 'var(--fp-600)',
  },
};

export function Button({
  variant = 'secondary', size = 'md', iconLeft, iconRight, loading, disabled,
  children, style, onClick, type = 'button', ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [active, setActive] = React.useState(false);
  const s = sizes[size]; const v = variants[variant];
  const bg = disabled ? 'var(--surface-sunken)' : (active ? v.activeBg : hover ? v.hoverBg : v.background);
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => { setHover(false); setActive(false); }}
      onMouseDown={() => setActive(true)}
      onMouseUp={() => setActive(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        gap: s.gap, height: s.h, padding: `0 ${s.px}px`, fontSize: s.fs,
        fontWeight: 'var(--fw-medium)', fontFamily: 'var(--font-sans)',
        border: v.border, borderRadius: s.r, background: bg,
        color: disabled ? 'var(--text-subtle)' : v.color,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out)',
        transform: active && !disabled ? 'scale(.98)' : 'scale(1)',
        whiteSpace: 'nowrap',
        ...style,
      }}
      {...rest}
    >
      {loading ? <Spinner size={s.fs} /> : iconLeft}
      {children}
      {iconRight}
    </button>
  );
}

function Spinner({ size }) {
  return (
    <span style={{
      width: size, height: size, border: '2px solid currentColor',
      borderTopColor: 'transparent', borderRadius: '50%',
      display: 'inline-block', animation: 'wf-spin 0.8s linear infinite'
    }} />
  );
}
