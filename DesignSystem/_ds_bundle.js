/* @ds-bundle: {"format":4,"namespace":"WaveformDesignSystem_606875","components":[{"name":"Card","sourcePath":"components/data/Card.jsx"},{"name":"KeyValue","sourcePath":"components/data/KeyValue.jsx"},{"name":"Tabs","sourcePath":"components/data/Tabs.jsx"},{"name":"ConversationTurn","sourcePath":"components/domain/ConversationTurn.jsx"},{"name":"Kbd","sourcePath":"components/domain/Kbd.jsx"},{"name":"StatCell","sourcePath":"components/domain/StatCell.jsx"},{"name":"ToolInvocation","sourcePath":"components/domain/ToolInvocation.jsx"},{"name":"Waveform","sourcePath":"components/domain/Waveform.jsx"},{"name":"Badge","sourcePath":"components/feedback/Badge.jsx"},{"name":"Dialog","sourcePath":"components/feedback/Dialog.jsx"},{"name":"WAKE_LABELS","sourcePath":"components/feedback/LabelChip.jsx"},{"name":"LabelChip","sourcePath":"components/feedback/LabelChip.jsx"},{"name":"Tag","sourcePath":"components/feedback/Tag.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Button","sourcePath":"components/forms/Button.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"IconButton","sourcePath":"components/forms/IconButton.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Radio","sourcePath":"components/forms/Radio.jsx"},{"name":"RadioGroup","sourcePath":"components/forms/Radio.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Textarea","sourcePath":"components/forms/Textarea.jsx"},{"name":"Sidebar","sourcePath":"components/nav/Sidebar.jsx"},{"name":"SidebarSection","sourcePath":"components/nav/Sidebar.jsx"},{"name":"SidebarItem","sourcePath":"components/nav/Sidebar.jsx"},{"name":"Toolbar","sourcePath":"components/nav/Toolbar.jsx"},{"name":"ToolbarSeparator","sourcePath":"components/nav/Toolbar.jsx"},{"name":"ToolbarSpacer","sourcePath":"components/nav/Toolbar.jsx"}],"sourceHashes":{"components/data/Card.jsx":"3016dc88fdb4","components/data/KeyValue.jsx":"551dd32ed131","components/data/Tabs.jsx":"3a1f67eb3af8","components/domain/ConversationTurn.jsx":"e3d70f77cbbb","components/domain/Kbd.jsx":"cbf030e602fe","components/domain/StatCell.jsx":"5a168b5787d8","components/domain/ToolInvocation.jsx":"b935f256624c","components/domain/Waveform.jsx":"6e9e51ab9e0d","components/feedback/Badge.jsx":"43674f41e7c1","components/feedback/Dialog.jsx":"590720332480","components/feedback/LabelChip.jsx":"783b21bc23b6","components/feedback/Tag.jsx":"4f29fd99cabc","components/feedback/Toast.jsx":"2d8a894f90bd","components/feedback/Tooltip.jsx":"5cedf28a333d","components/forms/Button.jsx":"69d89c919e18","components/forms/Checkbox.jsx":"d761cda7c238","components/forms/IconButton.jsx":"5b5834b445b4","components/forms/Input.jsx":"1e330763ee03","components/forms/Radio.jsx":"47b2d1c74118","components/forms/Select.jsx":"8681256f2a43","components/forms/Switch.jsx":"053c20d201b1","components/forms/Textarea.jsx":"f0abad3c7b14","components/nav/Sidebar.jsx":"f415f0645193","components/nav/Toolbar.jsx":"46631bea3aae","ui_kits/intent_training/Trainer.jsx":"117e0f9442b1","ui_kits/wake_word/Annotator.jsx":"84d7f7584453"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.WaveformDesignSystem_606875 = window.WaveformDesignSystem_606875 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/data/Card.jsx
try { (() => {
function Card({
  title,
  actions,
  footer,
  children,
  style,
  padded = true,
  elevation = 'flat'
}) {
  const shadow = elevation === 'raised' ? 'var(--shadow-sm)' : elevation === 'floating' ? 'var(--shadow-md)' : 'none';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface-panel)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--r-lg)',
      boxShadow: shadow,
      overflow: 'hidden',
      ...style
    }
  }, (title || actions) && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      padding: '10px 14px',
      borderBottom: '1px solid var(--border-subtle)',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 'var(--fw-semibold)',
      fontSize: 14,
      color: 'var(--text-body)',
      flex: 1
    }
  }, title), actions), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: padded ? 14 : 0
    }
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 14px',
      borderTop: '1px solid var(--border-subtle)',
      background: 'var(--surface-sunken)'
    }
  }, footer));
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Card.jsx", error: String((e && e.message) || e) }); }

// components/data/KeyValue.jsx
try { (() => {
function KeyValue({
  items = [],
  layout = 'rows',
  style
}) {
  if (layout === 'columns') {
    return /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: 16,
        ...style
      }
    }, items.map((it, i) => /*#__PURE__*/React.createElement("div", {
      key: i
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        textTransform: 'uppercase',
        letterSpacing: 'var(--tracking-caps)',
        color: 'var(--text-subtle)',
        marginBottom: 4
      }
    }, it.k), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 14,
        color: 'var(--text-body)',
        fontFamily: it.mono ? 'var(--font-mono)' : 'var(--font-sans)'
      }
    }, it.v))));
  }
  return /*#__PURE__*/React.createElement("dl", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'auto 1fr',
      gap: '8px 16px',
      margin: 0,
      ...style
    }
  }, items.map((it, i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: i
  }, /*#__PURE__*/React.createElement("dt", {
    style: {
      fontSize: 13,
      color: 'var(--text-muted)'
    }
  }, it.k), /*#__PURE__*/React.createElement("dd", {
    style: {
      margin: 0,
      fontSize: 13,
      color: 'var(--text-body)',
      fontFamily: it.mono ? 'var(--font-mono)' : 'var(--font-sans)'
    }
  }, it.v))));
}
Object.assign(__ds_scope, { KeyValue });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/KeyValue.jsx", error: String((e && e.message) || e) }); }

// components/data/Tabs.jsx
try { (() => {
function Tabs({
  tabs = [],
  value,
  onChange,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 2,
      borderBottom: '1px solid var(--border-subtle)',
      ...style
    }
  }, tabs.map(t => {
    const active = t.value === value;
    return /*#__PURE__*/React.createElement("button", {
      key: t.value,
      type: "button",
      onClick: () => onChange?.(t.value),
      style: {
        background: 'none',
        border: 'none',
        padding: '10px 12px',
        fontSize: 13,
        fontWeight: active ? 'var(--fw-semibold)' : 'var(--fw-medium)',
        color: active ? 'var(--text-body)' : 'var(--text-muted)',
        borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
        cursor: 'pointer',
        marginBottom: -1,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        transition: 'color var(--dur-fast)'
      }
    }, t.label, t.count != null && /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--text-subtle)',
        padding: '0 5px',
        background: 'var(--surface-hover)',
        borderRadius: 'var(--r-sm)'
      }
    }, t.count));
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/domain/ConversationTurn.jsx
try { (() => {
const roleStyles = {
  user: {
    align: 'flex-end',
    bg: 'var(--tn-050)',
    ink: 'var(--tn-600)',
    label: 'USER'
  },
  assistant: {
    align: 'flex-start',
    bg: 'var(--surface-panel)',
    ink: 'var(--text-body)',
    label: 'ASSISTANT'
  },
  tool: {
    align: 'flex-start',
    bg: 'var(--surface-sunken)',
    ink: 'var(--text-muted)',
    label: 'TOOL',
    mono: true
  },
  system: {
    align: 'center',
    bg: 'transparent',
    ink: 'var(--text-subtle)',
    label: 'SYSTEM',
    mono: true
  }
};
function ConversationTurn({
  role = 'user',
  name,
  timestamp,
  children,
  editable,
  onEdit,
  actions,
  style
}) {
  const r = roleStyles[role] || roleStyles.user;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: r.align,
      gap: 4,
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      fontSize: 11,
      letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase',
      color: r.ink,
      fontFamily: 'var(--font-mono)',
      fontWeight: 'var(--fw-medium)'
    }
  }, /*#__PURE__*/React.createElement("span", null, name || r.label), timestamp && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-subtle)'
    }
  }, timestamp)), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: '75%',
      minWidth: 60,
      padding: '8px 12px',
      background: r.bg,
      border: role === 'system' ? 'none' : '1px solid var(--border-subtle)',
      borderRadius: 'var(--r-md)',
      fontSize: 14,
      lineHeight: 'var(--lh-normal)',
      color: 'var(--text-body)',
      fontFamily: r.mono ? 'var(--font-mono)' : 'var(--font-sans)',
      whiteSpace: 'pre-wrap',
      position: 'relative'
    }
  }, children), actions && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      marginTop: 2
    }
  }, actions));
}
Object.assign(__ds_scope, { ConversationTurn });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/domain/ConversationTurn.jsx", error: String((e && e.message) || e) }); }

// components/domain/Kbd.jsx
try { (() => {
function Kbd({
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("kbd", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      padding: '1px 6px',
      borderRadius: 'var(--r-sm)',
      background: 'var(--surface-panel)',
      color: 'var(--text-muted)',
      border: '1px solid var(--border-default)',
      boxShadow: 'inset 0 -1px 0 var(--border-subtle)',
      whiteSpace: 'nowrap',
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Kbd });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/domain/Kbd.jsx", error: String((e && e.message) || e) }); }

// components/domain/StatCell.jsx
try { (() => {
function StatCell({
  label,
  value,
  delta,
  deltaTone = 'neutral',
  unit,
  style
}) {
  const tones = {
    neutral: 'var(--text-muted)',
    up: 'var(--tp-600)',
    down: 'var(--fp-600)'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      color: 'var(--text-subtle)'
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 24,
      fontWeight: 'var(--fw-semibold)',
      color: 'var(--text-body)',
      fontFamily: 'var(--font-mono)'
    }
  }, value), unit && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)'
    }
  }, unit)), delta && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: tones[deltaTone],
      fontFamily: 'var(--font-mono)'
    }
  }, delta));
}
Object.assign(__ds_scope, { StatCell });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/domain/StatCell.jsx", error: String((e && e.message) || e) }); }

// components/domain/ToolInvocation.jsx
try { (() => {
function ToolInvocation({
  name,
  args,
  result,
  status = 'ok',
  editable,
  onEditArgs,
  style
}) {
  const [open, setOpen] = React.useState(true);
  const statusTone = {
    ok: 'var(--tp-500)',
    pending: 'var(--fn-500)',
    error: 'var(--fp-500)'
  }[status];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--r-md)',
      background: 'var(--surface-sunken)',
      overflow: 'hidden',
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
      ...style
    }
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setOpen(o => !o),
    style: {
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 10px',
      background: 'transparent',
      border: 'none',
      cursor: 'pointer',
      color: 'var(--text-body)',
      borderBottom: open ? '1px solid var(--border-subtle)' : 'none',
      fontFamily: 'inherit',
      fontSize: 12,
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: statusTone
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 'var(--fw-semibold)'
    }
  }, name), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-subtle)',
      marginLeft: 'auto'
    }
  }, open ? '▾' : '▸')), open && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 10px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--text-subtle)',
      marginBottom: 2,
      fontSize: 10,
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)'
    }
  }, "Arguments"), /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: 0,
      whiteSpace: 'pre-wrap',
      color: 'var(--text-body)'
    }
  }, typeof args === 'string' ? args : JSON.stringify(args, null, 2))), result != null && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--text-subtle)',
      marginBottom: 2,
      fontSize: 10,
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)'
    }
  }, "Result"), /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: 0,
      whiteSpace: 'pre-wrap',
      color: 'var(--text-muted)'
    }
  }, typeof result === 'string' ? result : JSON.stringify(result, null, 2)))));
}
Object.assign(__ds_scope, { ToolInvocation });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/domain/ToolInvocation.jsx", error: String((e && e.message) || e) }); }

// components/domain/Waveform.jsx
try { (() => {
// Deterministic pseudo-random for stable rendering
function seedBars(seed, n, minH = 0.15, maxH = 1) {
  const arr = [];
  let s = seed;
  for (let i = 0; i < n; i++) {
    s = (s * 9301 + 49297) % 233280;
    const r = s / 233280;
    arr.push(minH + r * (maxH - minH));
  }
  return arr;
}
function Waveform({
  bars,
  samples = 64,
  seed = 42,
  playhead,
  // 0..1
  color,
  height = 56,
  barWidth = 3,
  barGap = 2,
  region,
  // { start, end } in 0..1 — highlight
  onScrub,
  style
}) {
  const data = bars || seedBars(seed, samples);
  const ref = React.useRef(null);
  const scrub = e => {
    if (!onScrub || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    onScrub(x);
  };
  const fill = color || 'var(--waveform-fill)';
  return /*#__PURE__*/React.createElement("div", {
    ref: ref,
    onClick: scrub,
    style: {
      position: 'relative',
      height,
      display: 'flex',
      alignItems: 'center',
      gap: barGap,
      cursor: onScrub ? 'pointer' : 'default',
      userSelect: 'none',
      ...style
    }
  }, region && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 0,
      bottom: 0,
      left: `${region.start * 100}%`,
      width: `${(region.end - region.start) * 100}%`,
      background: 'var(--accent-quiet)',
      borderLeft: '1px solid var(--accent)',
      borderRight: '1px solid var(--accent)',
      pointerEvents: 'none'
    }
  }), data.map((h, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      width: barWidth,
      height: `${h * 100}%`,
      minHeight: 2,
      background: playhead != null && i / data.length < playhead ? fill : 'var(--waveform-track)',
      borderRadius: 1,
      flex: '0 0 auto',
      transition: 'background var(--dur-fast)'
    }
  })), playhead != null && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: -2,
      bottom: -2,
      left: `${playhead * 100}%`,
      width: 2,
      background: 'var(--waveform-playhead)',
      pointerEvents: 'none'
    }
  }));
}
Object.assign(__ds_scope, { Waveform });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/domain/Waveform.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Badge.jsx
try { (() => {
const tones = {
  neutral: {
    bg: 'var(--surface-hover)',
    fg: 'var(--text-body)'
  },
  brand: {
    bg: 'var(--accent-quiet)',
    fg: 'var(--accent-active)'
  },
  tp: {
    bg: 'var(--tp-050)',
    fg: 'var(--tp-600)'
  },
  tn: {
    bg: 'var(--tn-050)',
    fg: 'var(--tn-600)'
  },
  fp: {
    bg: 'var(--fp-050)',
    fg: 'var(--fp-600)'
  },
  fn: {
    bg: 'var(--fn-050)',
    fg: 'var(--fn-600)'
  },
  bgnoise: {
    bg: 'var(--bg-050)',
    fg: 'var(--bg-600)'
  }
};
function Badge({
  tone = 'neutral',
  children,
  style,
  mono,
  dot
}) {
  const t = tones[tone] || tones.neutral;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '2px 8px',
      height: 20,
      borderRadius: 'var(--r-pill)',
      background: t.bg,
      color: t.fg,
      fontSize: 11,
      fontWeight: 'var(--fw-semibold)',
      letterSpacing: 'var(--tracking-wide)',
      fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)',
      textTransform: mono ? 'none' : 'uppercase',
      ...style
    }
  }, dot && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: 'currentColor'
    }
  }), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Badge.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Dialog.jsx
try { (() => {
function Dialog({
  open,
  onClose,
  title,
  children,
  footer,
  width = 480
}) {
  React.useEffect(() => {
    if (!open) return;
    const h = e => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [open, onClose]);
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": "true",
    style: {
      position: 'fixed',
      inset: 0,
      zIndex: 200,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--surface-overlay)',
      backdropFilter: 'blur(4px)'
    },
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      width,
      maxWidth: 'calc(100vw - 32px)',
      background: 'var(--surface-raised)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--r-lg)',
      boxShadow: 'var(--shadow-xl)',
      overflow: 'hidden'
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 16px',
      borderBottom: '1px solid var(--border-subtle)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 15
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 16,
      fontSize: 14,
      color: 'var(--text-body)',
      lineHeight: 'var(--lh-normal)'
    }
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 16px',
      borderTop: '1px solid var(--border-subtle)',
      background: 'var(--surface-sunken)',
      display: 'flex',
      justifyContent: 'flex-end',
      gap: 8
    }
  }, footer)));
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/feedback/LabelChip.jsx
try { (() => {
const WAKE_LABELS = [{
  id: 'tp',
  label: 'True positive',
  short: 'TP',
  tone: 'tp',
  key: '1'
}, {
  id: 'tn',
  label: 'True negative',
  short: 'TN',
  tone: 'tn',
  key: '2'
}, {
  id: 'fp',
  label: 'False positive',
  short: 'FP',
  tone: 'fp',
  key: '3'
}, {
  id: 'fn',
  label: 'False negative',
  short: 'FN',
  tone: 'fn',
  key: '4'
}, {
  id: 'bgnoise',
  label: 'Background noise',
  short: 'BG',
  tone: 'bgnoise',
  key: '5'
}];
const toneMap = {
  tp: {
    bg: 'var(--tp-500)',
    quiet: 'var(--tp-050)',
    ink: 'var(--tp-600)'
  },
  tn: {
    bg: 'var(--tn-500)',
    quiet: 'var(--tn-050)',
    ink: 'var(--tn-600)'
  },
  fp: {
    bg: 'var(--fp-500)',
    quiet: 'var(--fp-050)',
    ink: 'var(--fp-600)'
  },
  fn: {
    bg: 'var(--fn-500)',
    quiet: 'var(--fn-050)',
    ink: 'var(--fn-600)'
  },
  bgnoise: {
    bg: 'var(--bg-500)',
    quiet: 'var(--bg-050)',
    ink: 'var(--bg-600)'
  }
};
function LabelChip({
  tone = 'tp',
  selected,
  onClick,
  shortcut,
  children,
  style
}) {
  const t = toneMap[tone];
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      height: 30,
      padding: '0 10px 0 8px',
      border: selected ? `1.5px solid ${t.bg}` : '1.5px solid var(--border-default)',
      borderRadius: 'var(--r-md)',
      background: selected ? t.quiet : hover ? 'var(--surface-hover)' : 'var(--surface-panel)',
      color: selected ? t.ink : 'var(--text-body)',
      cursor: 'pointer',
      fontSize: 13,
      fontWeight: 'var(--fw-medium)',
      transition: 'all var(--dur-fast) var(--ease-out)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 10,
      height: 10,
      borderRadius: 2,
      background: t.bg,
      display: 'inline-block'
    }
  }), /*#__PURE__*/React.createElement("span", null, children), shortcut && /*#__PURE__*/React.createElement("kbd", {
    style: {
      marginLeft: 4,
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      padding: '1px 5px',
      borderRadius: 'var(--r-sm)',
      background: 'var(--surface-sunken)',
      color: 'var(--text-muted)',
      border: '1px solid var(--border-subtle)'
    }
  }, shortcut));
}
Object.assign(__ds_scope, { WAKE_LABELS, LabelChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/LabelChip.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tag.jsx
try { (() => {
function Tag({
  children,
  onRemove,
  style
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '2px 4px 2px 8px',
      height: 22,
      background: 'var(--surface-hover)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--r-sm)',
      fontSize: 12,
      color: 'var(--text-body)',
      fontFamily: 'var(--font-mono)',
      ...style
    }
  }, children, onRemove && /*#__PURE__*/React.createElement("button", {
    onClick: onRemove,
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--text-muted)',
      cursor: 'pointer',
      fontSize: 14,
      lineHeight: 1,
      padding: '0 2px'
    },
    "aria-label": "Remove"
  }, "\xD7"));
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tag.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
const toneMap = {
  info: {
    bar: 'var(--tn-500)',
    bg: 'var(--tn-050)'
  },
  success: {
    bar: 'var(--tp-500)',
    bg: 'var(--tp-050)'
  },
  warn: {
    bar: 'var(--fn-500)',
    bg: 'var(--fn-050)'
  },
  error: {
    bar: 'var(--fp-500)',
    bg: 'var(--fp-050)'
  }
};
function Toast({
  tone = 'info',
  title,
  description,
  onDismiss,
  style
}) {
  const t = toneMap[tone];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12,
      alignItems: 'flex-start',
      padding: '10px 12px',
      minWidth: 280,
      maxWidth: 420,
      background: 'var(--surface-raised)',
      border: '1px solid var(--border-subtle)',
      borderLeft: `3px solid ${t.bar}`,
      borderRadius: 'var(--r-md)',
      boxShadow: 'var(--shadow-lg)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 'var(--fw-semibold)',
      fontSize: 13,
      color: 'var(--text-body)',
      marginBottom: 2
    }
  }, title), description && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)',
      lineHeight: 'var(--lh-snug)'
    }
  }, description)), onDismiss && /*#__PURE__*/React.createElement("button", {
    onClick: onDismiss,
    "aria-label": "Dismiss",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--text-muted)',
      cursor: 'pointer',
      fontSize: 16,
      lineHeight: 1
    }
  }, "\xD7"));
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function Tooltip({
  content,
  placement = 'top',
  children,
  delay = 200
}) {
  const [open, setOpen] = React.useState(false);
  const t = React.useRef(null);
  const show = () => {
    clearTimeout(t.current);
    t.current = setTimeout(() => setOpen(true), delay);
  };
  const hide = () => {
    clearTimeout(t.current);
    setOpen(false);
  };
  const pos = {
    top: {
      bottom: '100%',
      left: '50%',
      transform: 'translate(-50%,-6px)'
    },
    bottom: {
      top: '100%',
      left: '50%',
      transform: 'translate(-50%,6px)'
    },
    left: {
      right: '100%',
      top: '50%',
      transform: 'translate(-6px,-50%)'
    },
    right: {
      left: '100%',
      top: '50%',
      transform: 'translate(6px,-50%)'
    }
  }[placement];
  return /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      display: 'inline-flex'
    },
    onMouseEnter: show,
    onMouseLeave: hide,
    onFocus: show,
    onBlur: hide
  }, children, open && /*#__PURE__*/React.createElement("span", {
    role: "tooltip",
    style: {
      position: 'absolute',
      ...pos,
      zIndex: 100,
      background: 'var(--surface-inverse)',
      color: 'var(--text-inverse)',
      padding: '5px 8px',
      borderRadius: 'var(--r-sm)',
      fontSize: 12,
      whiteSpace: 'nowrap',
      pointerEvents: 'none',
      boxShadow: 'var(--shadow-md)',
      fontFamily: 'var(--font-sans)'
    }
  }, content));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const sizes = {
  sm: {
    h: 28,
    px: 10,
    fs: 13,
    gap: 6,
    r: 'var(--r-md)'
  },
  md: {
    h: 34,
    px: 14,
    fs: 14,
    gap: 8,
    r: 'var(--r-md)'
  },
  lg: {
    h: 42,
    px: 18,
    fs: 15,
    gap: 10,
    r: 'var(--r-lg)'
  }
};
const variants = {
  primary: {
    background: 'var(--accent)',
    color: 'var(--text-on-brand)',
    border: '1px solid transparent',
    hoverBg: 'var(--accent-hover)',
    activeBg: 'var(--accent-active)'
  },
  secondary: {
    background: 'var(--surface-panel)',
    color: 'var(--text-body)',
    border: '1px solid var(--border-default)',
    hoverBg: 'var(--surface-hover)',
    activeBg: 'var(--surface-active)'
  },
  ghost: {
    background: 'transparent',
    color: 'var(--text-body)',
    border: '1px solid transparent',
    hoverBg: 'var(--surface-hover)',
    activeBg: 'var(--surface-active)'
  },
  danger: {
    background: 'var(--fp-500)',
    color: '#fff',
    border: '1px solid transparent',
    hoverBg: 'var(--fp-600)',
    activeBg: 'var(--fp-600)'
  }
};
function Button({
  variant = 'secondary',
  size = 'md',
  iconLeft,
  iconRight,
  loading,
  disabled,
  children,
  style,
  onClick,
  type = 'button',
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [active, setActive] = React.useState(false);
  const s = sizes[size];
  const v = variants[variant];
  const bg = disabled ? 'var(--surface-sunken)' : active ? v.activeBg : hover ? v.hoverBg : v.background;
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    onClick: onClick,
    disabled: disabled || loading,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => {
      setHover(false);
      setActive(false);
    },
    onMouseDown: () => setActive(true),
    onMouseUp: () => setActive(false),
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: s.gap,
      height: s.h,
      padding: `0 ${s.px}px`,
      fontSize: s.fs,
      fontWeight: 'var(--fw-medium)',
      fontFamily: 'var(--font-sans)',
      border: v.border,
      borderRadius: s.r,
      background: bg,
      color: disabled ? 'var(--text-subtle)' : v.color,
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out)',
      transform: active && !disabled ? 'scale(.98)' : 'scale(1)',
      whiteSpace: 'nowrap',
      ...style
    }
  }, rest), loading ? /*#__PURE__*/React.createElement(Spinner, {
    size: s.fs
  }) : iconLeft, children, iconRight);
}
function Spinner({
  size
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      width: size,
      height: size,
      border: '2px solid currentColor',
      borderTopColor: 'transparent',
      borderRadius: '50%',
      display: 'inline-block',
      animation: 'wf-spin 0.8s linear infinite'
    }
  });
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Button.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function Checkbox({
  checked,
  indeterminate,
  onChange,
  label,
  disabled,
  id,
  style
}) {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (ref.current) ref.current.indeterminate = !!indeterminate;
  }, [indeterminate]);
  const box = /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      display: 'inline-block',
      width: 16,
      height: 16
    }
  }, /*#__PURE__*/React.createElement("input", {
    ref: ref,
    id: id,
    type: "checkbox",
    checked: !!checked,
    disabled: disabled,
    onChange: e => onChange?.(e.target.checked, e),
    style: {
      appearance: 'none',
      WebkitAppearance: 'none',
      width: 16,
      height: 16,
      margin: 0,
      border: `1.5px solid ${checked || indeterminate ? 'var(--accent)' : 'var(--border-strong)'}`,
      borderRadius: 'var(--r-sm)',
      background: checked || indeterminate ? 'var(--accent)' : 'var(--surface-panel)',
      cursor: disabled ? 'not-allowed' : 'pointer',
      display: 'block',
      transition: 'background var(--dur-fast), border-color var(--dur-fast)'
    }
  }), (checked || indeterminate) && /*#__PURE__*/React.createElement("span", {
    "aria-hidden": true,
    style: {
      position: 'absolute',
      inset: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--text-on-brand)',
      fontSize: 11,
      fontWeight: 700,
      pointerEvents: 'none'
    }
  }, indeterminate ? '–' : '✓'));
  if (!label) return box;
  return /*#__PURE__*/React.createElement("label", {
    htmlFor: id,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      cursor: disabled ? 'not-allowed' : 'pointer',
      color: 'var(--text-body)',
      fontSize: 14,
      ...style
    }
  }, box, /*#__PURE__*/React.createElement("span", null, label));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const sz = {
  sm: 26,
  md: 32,
  lg: 40
};
function IconButton({
  size = 'md',
  variant = 'ghost',
  active,
  disabled,
  children,
  style,
  onClick,
  'aria-label': al,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const s = sz[size];
  const isBrand = variant === 'primary';
  const bg = disabled ? 'transparent' : active ? isBrand ? 'var(--accent-active)' : 'var(--surface-active)' : hover ? isBrand ? 'var(--accent-hover)' : 'var(--surface-hover)' : isBrand ? 'var(--accent)' : 'transparent';
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    "aria-label": al,
    onClick: onClick,
    disabled: disabled,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      width: s,
      height: s,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      border: variant === 'outline' ? '1px solid var(--border-default)' : 'none',
      background: bg,
      color: isBrand ? 'var(--text-on-brand)' : disabled ? 'var(--text-subtle)' : 'var(--text-body)',
      borderRadius: 'var(--r-md)',
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'background var(--dur-fast) var(--ease-out)',
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const sz = {
  sm: {
    h: 28,
    fs: 13,
    px: 8
  },
  md: {
    h: 34,
    fs: 14,
    px: 10
  },
  lg: {
    h: 42,
    fs: 15,
    px: 12
  }
};
function Input({
  size = 'md',
  invalid,
  prefix,
  suffix,
  style,
  disabled,
  ...rest
}) {
  const [focus, setFocus] = React.useState(false);
  const s = sz[size];
  const border = invalid ? 'var(--fp-500)' : focus ? 'var(--border-focus)' : 'var(--border-default)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      height: s.h,
      background: disabled ? 'var(--surface-sunken)' : 'var(--surface-panel)',
      border: `1px solid ${border}`,
      borderRadius: 'var(--r-md)',
      boxShadow: focus ? 'var(--shadow-focus)' : 'none',
      transition: 'border-color var(--dur-fast), box-shadow var(--dur-fast)',
      padding: `0 ${s.px}px`,
      ...style
    }
  }, prefix && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)',
      display: 'inline-flex',
      marginRight: 6
    }
  }, prefix), /*#__PURE__*/React.createElement("input", _extends({}, rest, {
    disabled: disabled,
    onFocus: e => {
      setFocus(true);
      rest.onFocus?.(e);
    },
    onBlur: e => {
      setFocus(false);
      rest.onBlur?.(e);
    },
    style: {
      flex: 1,
      height: '100%',
      border: 'none',
      outline: 'none',
      background: 'transparent',
      fontSize: s.fs,
      color: 'var(--text-body)',
      fontFamily: 'var(--font-sans)',
      minWidth: 0
    }
  })), suffix && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-muted)',
      display: 'inline-flex',
      marginLeft: 6
    }
  }, suffix));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Radio.jsx
try { (() => {
function Radio({
  checked,
  onChange,
  label,
  name,
  value,
  disabled,
  id,
  style
}) {
  const dot = /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      display: 'inline-block',
      width: 16,
      height: 16
    }
  }, /*#__PURE__*/React.createElement("input", {
    id: id,
    type: "radio",
    name: name,
    value: value,
    checked: !!checked,
    disabled: disabled,
    onChange: e => onChange?.(e),
    style: {
      appearance: 'none',
      WebkitAppearance: 'none',
      width: 16,
      height: 16,
      margin: 0,
      border: `1.5px solid ${checked ? 'var(--accent)' : 'var(--border-strong)'}`,
      borderRadius: 'var(--r-pill)',
      background: 'var(--surface-panel)',
      cursor: disabled ? 'not-allowed' : 'pointer',
      display: 'block'
    }
  }), checked && /*#__PURE__*/React.createElement("span", {
    "aria-hidden": true,
    style: {
      position: 'absolute',
      inset: 4,
      background: 'var(--accent)',
      borderRadius: 'var(--r-pill)'
    }
  }));
  if (!label) return dot;
  return /*#__PURE__*/React.createElement("label", {
    htmlFor: id,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      cursor: disabled ? 'not-allowed' : 'pointer',
      color: 'var(--text-body)',
      fontSize: 14,
      ...style
    }
  }, dot, /*#__PURE__*/React.createElement("span", null, label));
}
function RadioGroup({
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Radio, RadioGroup });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Radio.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const sz = {
  sm: {
    h: 28,
    fs: 13
  },
  md: {
    h: 34,
    fs: 14
  },
  lg: {
    h: 42,
    fs: 15
  }
};
function Select({
  size = 'md',
  invalid,
  options = [],
  value,
  onChange,
  style,
  disabled,
  ...rest
}) {
  const [focus, setFocus] = React.useState(false);
  const s = sz[size];
  const border = invalid ? 'var(--fp-500)' : focus ? 'var(--border-focus)' : 'var(--border-default)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      display: 'inline-flex',
      width: style?.width || 'auto'
    }
  }, /*#__PURE__*/React.createElement("select", _extends({
    value: value,
    onChange: onChange,
    disabled: disabled
  }, rest, {
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      height: s.h,
      fontSize: s.fs,
      fontFamily: 'var(--font-sans)',
      padding: '0 28px 0 10px',
      appearance: 'none',
      WebkitAppearance: 'none',
      background: disabled ? 'var(--surface-sunken)' : 'var(--surface-panel)',
      border: `1px solid ${border}`,
      borderRadius: 'var(--r-md)',
      color: 'var(--text-body)',
      outline: 'none',
      width: '100%',
      boxShadow: focus ? 'var(--shadow-focus)' : 'none',
      transition: 'border-color var(--dur-fast)',
      ...style
    }
  }), options.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label))), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": true,
    style: {
      position: 'absolute',
      right: 8,
      top: '50%',
      transform: 'translateY(-50%)',
      color: 'var(--text-muted)',
      pointerEvents: 'none',
      fontSize: 10
    }
  }, "\u25BE"));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function Switch({
  checked,
  onChange,
  label,
  disabled,
  style
}) {
  const track = /*#__PURE__*/React.createElement("span", {
    onClick: () => !disabled && onChange?.(!checked),
    style: {
      width: 32,
      height: 18,
      borderRadius: 'var(--r-pill)',
      background: checked ? 'var(--accent)' : 'var(--gray-300)',
      position: 'relative',
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'background var(--dur-fast)',
      flexShrink: 0,
      opacity: disabled ? .5 : 1
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      top: 2,
      left: checked ? 16 : 2,
      width: 14,
      height: 14,
      borderRadius: 'var(--r-pill)',
      background: '#fff',
      boxShadow: 'var(--shadow-sm)',
      transition: 'left var(--dur-fast) var(--ease-out)'
    }
  }));
  if (!label) return track;
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 10,
      cursor: disabled ? 'not-allowed' : 'pointer',
      color: 'var(--text-body)',
      fontSize: 14,
      ...style
    }
  }, track, /*#__PURE__*/React.createElement("span", null, label));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/forms/Textarea.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function Textarea({
  invalid,
  style,
  disabled,
  minRows = 3,
  ...rest
}) {
  const [focus, setFocus] = React.useState(false);
  const border = invalid ? 'var(--fp-500)' : focus ? 'var(--border-focus)' : 'var(--border-default)';
  return /*#__PURE__*/React.createElement("textarea", _extends({}, rest, {
    disabled: disabled,
    rows: minRows,
    onFocus: e => {
      setFocus(true);
      rest.onFocus?.(e);
    },
    onBlur: e => {
      setFocus(false);
      rest.onBlur?.(e);
    },
    style: {
      width: '100%',
      padding: '8px 10px',
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      lineHeight: 'var(--lh-normal)',
      color: 'var(--text-body)',
      background: disabled ? 'var(--surface-sunken)' : 'var(--surface-panel)',
      border: `1px solid ${border}`,
      borderRadius: 'var(--r-md)',
      boxShadow: focus ? 'var(--shadow-focus)' : 'none',
      outline: 'none',
      resize: 'vertical',
      transition: 'border-color var(--dur-fast), box-shadow var(--dur-fast)',
      ...style
    }
  }));
}
Object.assign(__ds_scope, { Textarea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Textarea.jsx", error: String((e && e.message) || e) }); }

// components/nav/Sidebar.jsx
try { (() => {
function Sidebar({
  children,
  width = 232,
  style
}) {
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width,
      minWidth: width,
      height: '100%',
      background: 'var(--surface-panel)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      fontSize: 13,
      color: 'var(--text-body)',
      ...style
    }
  }, children);
}
function SidebarSection({
  title,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 8px 4px',
      ...style
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 8px 6px',
      fontSize: 10,
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      color: 'var(--text-subtle)',
      fontWeight: 'var(--fw-semibold)'
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 1
    }
  }, children));
}
function SidebarItem({
  icon,
  active,
  badge,
  children,
  onClick,
  style
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      width: '100%',
      padding: '6px 8px',
      border: 'none',
      textAlign: 'left',
      background: active ? 'var(--accent-quiet)' : hover ? 'var(--surface-hover)' : 'transparent',
      color: active ? 'var(--accent-active)' : 'var(--text-body)',
      borderRadius: 'var(--r-md)',
      cursor: 'pointer',
      fontSize: 13,
      fontFamily: 'var(--font-sans)',
      fontWeight: active ? 'var(--fw-semibold)' : 'var(--fw-regular)',
      transition: 'background var(--dur-fast)',
      ...style
    }
  }, icon && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 16,
      height: 16,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: active ? 'var(--accent-active)' : 'var(--text-muted)'
    }
  }, icon), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      minWidth: 0,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, children), badge != null && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontFamily: 'var(--font-mono)',
      color: 'var(--text-muted)',
      padding: '0 5px',
      background: 'var(--surface-hover)',
      borderRadius: 'var(--r-sm)'
    }
  }, badge));
}
Object.assign(__ds_scope, { Sidebar, SidebarSection, SidebarItem });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/nav/Sidebar.jsx", error: String((e && e.message) || e) }); }

// components/nav/Toolbar.jsx
try { (() => {
function Toolbar({
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 12px',
      minHeight: 48,
      background: 'var(--surface-panel)',
      borderBottom: '1px solid var(--border-subtle)',
      ...style
    }
  }, children);
}
function ToolbarSeparator() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 1,
      height: 20,
      background: 'var(--border-default)',
      margin: '0 4px'
    }
  });
}
function ToolbarSpacer() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  });
}
Object.assign(__ds_scope, { Toolbar, ToolbarSeparator, ToolbarSpacer });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/nav/Toolbar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/intent_training/Trainer.jsx
try { (() => {
const {
  Sidebar,
  SidebarSection,
  SidebarItem,
  Toolbar,
  ToolbarSeparator,
  ToolbarSpacer,
  Button,
  IconButton,
  Badge,
  Card,
  Tabs,
  KeyValue,
  Input,
  Textarea,
  Kbd,
  StatCell,
  ConversationTurn,
  ToolInvocation,
  Tag,
  Switch,
  Tooltip
} = window.WaveformDesignSystem_606875;
const Ico = ({
  d,
  size = 14
}) => /*#__PURE__*/React.createElement("svg", {
  width: size,
  height: size,
  viewBox: "0 0 16 16",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "1.5",
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, d.split('|').map((p, i) => /*#__PURE__*/React.createElement("path", {
  key: i,
  d: p
})));
const sessions = [{
  id: 's_2a4b',
  device: 'kitchen_hub',
  time: '11:24',
  intent: 'lights.set',
  flagged: false
}, {
  id: 's_2a4c',
  device: 'bedroom_pixel',
  time: '11:26',
  intent: 'timer.start',
  flagged: true
}, {
  id: 's_2a4d',
  device: 'office_dot',
  time: '11:31',
  intent: 'music.play',
  flagged: false
}, {
  id: 's_2a4e',
  device: 'car_mount',
  time: '11:44',
  intent: 'navigation.start',
  flagged: false
}, {
  id: 's_2a4f',
  device: 'kitchen_hub',
  time: '12:02',
  intent: 'lights.set',
  flagged: false
}, {
  id: 's_2a50',
  device: 'living_hub',
  time: '12:19',
  intent: 'weather.query',
  flagged: false
}, {
  id: 's_2a51',
  device: 'kitchen_hub',
  time: '12:33',
  intent: 'unknown',
  flagged: true
}];
function Trainer() {
  const [selId, setSelId] = React.useState('s_2a4b');
  const [tab, setTab] = React.useState('all');
  const [theme, setTheme] = React.useState('light');
  const [notes, setNotes] = React.useState('User expected the light to dim gradually — original response was too abrupt. Edited to explicitly acknowledge the "slowly" qualifier.');
  const [assistantText, setAssistantText] = React.useState('Turning on the kitchen lights, easing to 40% over 2 seconds.');
  const [toolArgs, setToolArgs] = React.useState('{\n  "room": "kitchen",\n  "on": true,\n  "brightness": 40,\n  "transition_ms": 2000\n}');
  return /*#__PURE__*/React.createElement("div", {
    "data-theme": theme,
    style: {
      display: 'flex',
      height: '100vh',
      background: 'var(--surface-app)',
      color: 'var(--text-body)',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement(Sidebar, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 12px',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "2",
    y: "10",
    width: "2",
    height: "4",
    fill: "var(--brand-500)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "6",
    y: "6",
    width: "2",
    height: "12",
    fill: "var(--brand-500)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "10",
    y: "2",
    width: "2",
    height: "20",
    fill: "var(--brand-400)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "6",
    width: "2",
    height: "12",
    fill: "var(--brand-400)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "18",
    y: "10",
    width: "2",
    height: "4",
    fill: "var(--brand-300)"
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      fontSize: 14,
      letterSpacing: -0.02
    }
  }, "Intentsity")), /*#__PURE__*/React.createElement(SidebarSection, {
    title: "Workspaces"
  }, /*#__PURE__*/React.createElement(SidebarItem, {
    icon: /*#__PURE__*/React.createElement(Ico, {
      d: "M2 8h12M8 2v12"
    }),
    badge: 128
  }, "Wake word"), /*#__PURE__*/React.createElement(SidebarItem, {
    icon: /*#__PURE__*/React.createElement(Ico, {
      d: "M2 4h12M2 8h12M2 12h8"
    }),
    active: true,
    badge: 42
  }, "Intent training")), /*#__PURE__*/React.createElement(SidebarSection, {
    title: "Intent taxonomy"
  }, /*#__PURE__*/React.createElement(SidebarItem, {
    icon: /*#__PURE__*/React.createElement(Ico, {
      d: "M8 2v12M2 8h12",
      size: 11
    }),
    active: true,
    badge: 14
  }, "lights.set"), /*#__PURE__*/React.createElement(SidebarItem, {
    badge: 8
  }, "timer.start"), /*#__PURE__*/React.createElement(SidebarItem, {
    badge: 6
  }, "music.play"), /*#__PURE__*/React.createElement(SidebarItem, {
    badge: 4
  }, "navigation.start"), /*#__PURE__*/React.createElement(SidebarItem, {
    badge: 3
  }, "weather.query"), /*#__PURE__*/React.createElement(SidebarItem, {
    badge: 7
  }, "unknown")), /*#__PURE__*/React.createElement(SidebarSection, {
    title: "Fine-tune runs"
  }, /*#__PURE__*/React.createElement(SidebarItem, null, "atlas-llm-v1.4 \xB7 queued"), /*#__PURE__*/React.createElement(SidebarItem, null, "atlas-llm-v1.3 \xB7 deployed"))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(Toolbar, null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)'
    }
  }, "Intent"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--text-subtle)'
    }
  }, "/"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      fontSize: 14,
      fontFamily: 'var(--font-mono)'
    }
  }, "lights.set"), /*#__PURE__*/React.createElement(Badge, {
    tone: "brand"
  }, "14 sessions"), /*#__PURE__*/React.createElement(ToolbarSeparator, null), /*#__PURE__*/React.createElement(Input, {
    size: "sm",
    placeholder: "Search transcripts\u2026",
    style: {
      width: 240
    },
    prefix: /*#__PURE__*/React.createElement(Ico, {
      d: "M7 2a5 5 0 100 10 5 5 0 000-10zM11.5 11.5L14 14",
      size: 12
    })
  }), /*#__PURE__*/React.createElement(ToolbarSpacer, null), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "ghost",
    iconLeft: /*#__PURE__*/React.createElement(Ico, {
      d: "M3 8h10M8 3v10",
      size: 11
    })
  }, "Add example"), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "primary"
  }, "Queue fine-tune")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 280,
      minWidth: 280,
      borderRight: '1px solid var(--border-subtle)',
      background: 'var(--surface-panel)',
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 12px',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    value: tab,
    onChange: setTab,
    tabs: [{
      value: 'all',
      label: 'All',
      count: 14
    }, {
      value: 'flagged',
      label: 'Flagged',
      count: 2
    }, {
      value: 'edited',
      label: 'Edited',
      count: 5
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto'
    }
  }, sessions.map(s => {
    const active = s.id === selId;
    return /*#__PURE__*/React.createElement("button", {
      key: s.id,
      onClick: () => setSelId(s.id),
      style: {
        display: 'block',
        width: '100%',
        padding: '12px 14px',
        border: 'none',
        textAlign: 'left',
        background: active ? 'var(--accent-quiet)' : 'transparent',
        borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
        borderBottom: '1px solid var(--border-subtle)',
        cursor: 'pointer',
        color: 'var(--text-body)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 4
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        fontWeight: 500
      }
    }, s.id), s.flagged && /*#__PURE__*/React.createElement(Badge, {
      tone: "fn",
      dot: true,
      style: {
        height: 16,
        fontSize: 9
      }
    }, "flag")), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        color: 'var(--text-body)',
        marginBottom: 2,
        fontFamily: 'var(--font-mono)'
      }
    }, s.intent), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: 'var(--text-muted)'
      }
    }, s.device, " \xB7 ", s.time));
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: 24,
      overflow: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 18,
      fontWeight: 600
    }
  }, "Session ", selId), /*#__PURE__*/React.createElement(Badge, {
    mono: true
  }, "lights.set"), /*#__PURE__*/React.createElement(Tag, null, "device=kitchen_hub"), /*#__PURE__*/React.createElement(Tag, null, "lang=en-US"), /*#__PURE__*/React.createElement(ToolbarSpacer, null), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "ghost"
  }, "Discard edits")), /*#__PURE__*/React.createElement(ConversationTurn, {
    role: "system",
    timestamp: "turn 0"
  }, "Session started \xB7 kitchen_hub \xB7 12:02:14"), /*#__PURE__*/React.createElement(ConversationTurn, {
    role: "user",
    timestamp: "0.4s"
  }, "turn on the kitchen lights, slowly"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--text-subtle)',
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      fontWeight: 600,
      marginBottom: 6,
      fontFamily: 'var(--font-mono)'
    }
  }, "Tool call \u2014 editable"), /*#__PURE__*/React.createElement(ToolInvocation, {
    name: "lights.set",
    status: "ok",
    args: toolArgs,
    result: {
      ok: true,
      applied_at: '0.9s'
    }
  }), /*#__PURE__*/React.createElement(Textarea, {
    style: {
      marginTop: 8,
      fontFamily: 'var(--font-mono)',
      fontSize: 12
    },
    minRows: 5,
    value: toolArgs,
    onChange: e => setToolArgs(e.target.value)
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--text-subtle)',
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      fontWeight: 600,
      marginBottom: 6,
      fontFamily: 'var(--font-mono)'
    }
  }, "Assistant response \u2014 editable"), /*#__PURE__*/React.createElement(ConversationTurn, {
    role: "assistant",
    timestamp: "1.1s"
  }, assistantText), /*#__PURE__*/React.createElement(Textarea, {
    style: {
      marginTop: 8
    },
    minRows: 2,
    value: assistantText,
    onChange: e => setAssistantText(e.target.value)
  })), /*#__PURE__*/React.createElement(ConversationTurn, {
    role: "user",
    timestamp: "4.2s"
  }, "that's perfect, thanks"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--text-subtle)',
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      fontWeight: 600,
      marginBottom: 6,
      fontFamily: 'var(--font-mono)'
    }
  }, "Trainer notes"), /*#__PURE__*/React.createElement(Textarea, {
    minRows: 3,
    value: notes,
    onChange: e => setNotes(e.target.value)
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      paddingTop: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary"
  }, "Save & next"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost"
  }, "Skip"), /*#__PURE__*/React.createElement(ToolbarSpacer, null), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)',
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Kbd, null, "\u2318S"), " save", /*#__PURE__*/React.createElement(Kbd, null, "\u2318\u21E7F"), " flag"))), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 280,
      minWidth: 280,
      borderLeft: '1px solid var(--border-subtle)',
      background: 'var(--surface-panel)',
      padding: 16,
      overflow: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--text-subtle)',
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      fontWeight: 600,
      marginBottom: 10
    }
  }, "Intent metadata"), /*#__PURE__*/React.createElement(KeyValue, {
    items: [{
      k: 'Intent',
      v: 'lights.set',
      mono: true
    }, {
      k: 'Confidence',
      v: '0.94',
      mono: true
    }, {
      k: 'Slots',
      v: 'room, brightness, transition'
    }, {
      k: 'LLM version',
      v: 'atlas-llm-v1.3',
      mono: true
    }, {
      k: 'Device',
      v: 'kitchen_hub'
    }]
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--text-subtle)',
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      fontWeight: 600,
      marginBottom: 10
    }
  }, "Slot values"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Tag, null, "room=kitchen"), /*#__PURE__*/React.createElement(Tag, null, "brightness=40"), /*#__PURE__*/React.createElement(Tag, null, "transition_ms=2000"))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--text-subtle)',
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      fontWeight: 600,
      marginBottom: 10
    }
  }, "Training impact"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement(StatCell, {
    label: "Similar",
    value: "42",
    unit: "sessions"
  }), /*#__PURE__*/React.createElement(StatCell, {
    label: "Precision",
    value: "0.941",
    delta: "+0.03",
    deltaTone: "up"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Switch, {
    label: "Include in next fine-tune",
    defaultChecked: true
  }), /*#__PURE__*/React.createElement(Switch, {
    label: "Use as golden example"
  })))))));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(Trainer, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/intent_training/Trainer.jsx", error: String((e && e.message) || e) }); }

// ui_kits/wake_word/Annotator.jsx
try { (() => {
const {
  Sidebar,
  SidebarSection,
  SidebarItem,
  Toolbar,
  ToolbarSeparator,
  ToolbarSpacer,
  Button,
  IconButton,
  Badge,
  LabelChip,
  WAKE_LABELS,
  Waveform,
  Card,
  Tabs,
  KeyValue,
  Input,
  Checkbox,
  Kbd,
  StatCell,
  Switch,
  Tooltip
} = window.WaveformDesignSystem_606875;

// --- Icons ---
const Ico = ({
  d,
  size = 14
}) => /*#__PURE__*/React.createElement("svg", {
  width: size,
  height: size,
  viewBox: "0 0 16 16",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "1.5",
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, d.split('|').map((p, i) => /*#__PURE__*/React.createElement("path", {
  key: i,
  d: p
})));
const PlayIcon = () => /*#__PURE__*/React.createElement("svg", {
  width: "12",
  height: "12",
  viewBox: "0 0 12 12",
  fill: "currentColor"
}, /*#__PURE__*/React.createElement("path", {
  d: "M3 2l7 4-7 4V2z"
}));
const PauseIcon = () => /*#__PURE__*/React.createElement("svg", {
  width: "12",
  height: "12",
  viewBox: "0 0 12 12",
  fill: "currentColor"
}, /*#__PURE__*/React.createElement("rect", {
  x: "3",
  y: "2",
  width: "2",
  height: "8"
}), /*#__PURE__*/React.createElement("rect", {
  x: "7",
  y: "2",
  width: "2",
  height: "8"
}));

// --- Fake data ---
const seedRand = s => {
  let x = s;
  return () => {
    x = (x * 9301 + 49297) % 233280;
    return x / 233280;
  };
};
function makeClip(i, seed) {
  const r = seedRand(seed + i);
  return {
    id: 'c_' + (seed * 7 + i).toString(16).padStart(8, '0'),
    duration: (0.6 + r() * 1.4).toFixed(2),
    confidence: (0.4 + r() * 0.55).toFixed(2),
    device: ['kitchen_hub', 'bedroom_pixel', 'office_dot', 'car_mount'][Math.floor(r() * 4)],
    time: `${Math.floor(r() * 23)}:${String(Math.floor(r() * 59)).padStart(2, '0')}`,
    seed: seed * 13 + i,
    label: null
  };
}
const initialClips = Array.from({
  length: 24
}, (_, i) => makeClip(i, 42));
function Annotator() {
  const [clips, setClips] = React.useState(initialClips);
  const [selIdx, setSelIdx] = React.useState(0);
  const [playing, setPlaying] = React.useState(false);
  const [playhead, setPlayhead] = React.useState(0.32);
  const [tab, setTab] = React.useState('unlabeled');
  const [autoAdvance, setAutoAdvance] = React.useState(true);
  const [theme, setTheme] = React.useState('light');
  const clip = clips[selIdx];
  React.useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setPlayhead(p => p >= 1 ? (setPlaying(false), 0) : p + 0.01), 30);
    return () => clearInterval(id);
  }, [playing]);
  const setLabel = labelId => {
    setClips(cs => cs.map((c, i) => i === selIdx ? {
      ...c,
      label: labelId
    } : c));
    if (autoAdvance) setTimeout(() => {
      setSelIdx(i => Math.min(clips.length - 1, i + 1));
      setPlayhead(0);
      setPlaying(false);
    }, 100);
  };

  // Keyboard
  React.useEffect(() => {
    const h = e => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      const num = ['1', '2', '3', '4', '5'].indexOf(e.key);
      if (num >= 0) {
        setLabel(WAKE_LABELS[num].id);
        return;
      }
      if (e.key === ' ') {
        e.preventDefault();
        setPlaying(p => !p);
        return;
      }
      if (e.key === 'j' || e.key === 'ArrowDown') setSelIdx(i => Math.min(clips.length - 1, i + 1));
      if (e.key === 'k' || e.key === 'ArrowUp') setSelIdx(i => Math.max(0, i - 1));
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  });
  const counts = clips.reduce((a, c) => (c.label ? a.labeled++ : a.unlabeled++, a), {
    labeled: 0,
    unlabeled: 0,
    flagged: 0
  });
  return /*#__PURE__*/React.createElement("div", {
    "data-theme": theme,
    style: {
      display: 'flex',
      height: '100vh',
      background: 'var(--surface-app)',
      color: 'var(--text-body)',
      fontFamily: 'var(--font-sans)'
    }
  }, /*#__PURE__*/React.createElement(Sidebar, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 12px',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "2",
    y: "10",
    width: "2",
    height: "4",
    fill: "var(--brand-500)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "6",
    y: "6",
    width: "2",
    height: "12",
    fill: "var(--brand-500)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "10",
    y: "2",
    width: "2",
    height: "20",
    fill: "var(--brand-400)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "6",
    width: "2",
    height: "12",
    fill: "var(--brand-400)"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "18",
    y: "10",
    width: "2",
    height: "4",
    fill: "var(--brand-300)"
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      fontSize: 14,
      letterSpacing: -0.02
    }
  }, "Intentsity")), /*#__PURE__*/React.createElement(SidebarSection, {
    title: "Workspaces"
  }, /*#__PURE__*/React.createElement(SidebarItem, {
    icon: /*#__PURE__*/React.createElement(Ico, {
      d: "M2 8h12M8 2v12"
    }),
    active: true,
    badge: counts.unlabeled
  }, "Wake word"), /*#__PURE__*/React.createElement(SidebarItem, {
    icon: /*#__PURE__*/React.createElement(Ico, {
      d: "M2 4h12M2 8h12M2 12h8"
    }),
    badge: 42
  }, "Intent training")), /*#__PURE__*/React.createElement(SidebarSection, {
    title: "Datasets"
  }, /*#__PURE__*/React.createElement(SidebarItem, {
    active: true
  }, "hey-atlas / prod"), /*#__PURE__*/React.createElement(SidebarItem, null, "hey-atlas / edge cases"), /*#__PURE__*/React.createElement(SidebarItem, null, "ok-atlas / prod"), /*#__PURE__*/React.createElement(SidebarItem, null, "alexa-baseline")), /*#__PURE__*/React.createElement(SidebarSection, {
    title: "Models"
  }, /*#__PURE__*/React.createElement(SidebarItem, {
    icon: /*#__PURE__*/React.createElement(Ico, {
      d: "M8 2v12M2 8h12"
    })
  }, "wake-atlas-v3.2.1"), /*#__PURE__*/React.createElement(SidebarItem, null, "wake-atlas-v2.4.0")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 'auto',
      padding: '10px 12px',
      borderTop: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      fontSize: 12,
      color: 'var(--text-muted)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 26,
      height: 26,
      borderRadius: '50%',
      background: 'var(--brand-500)',
      color: 'var(--text-on-brand)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 11,
      fontWeight: 600
    }
  }, "MJ"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--text-body)',
      fontSize: 12,
      fontWeight: 500
    }
  }, "maria.jansen"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11
    }
  }, "Voice ML team")), /*#__PURE__*/React.createElement(Tooltip, {
    content: "Toggle theme"
  }, /*#__PURE__*/React.createElement(IconButton, {
    size: "sm",
    "aria-label": "theme",
    onClick: () => setTheme(t => t === 'light' ? 'dark' : 'light')
  }, /*#__PURE__*/React.createElement(Ico, {
    d: "M8 2v2|M8 12v2|M2 8h2|M12 8h2",
    size: 12
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(Toolbar, null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)'
    }
  }, "Datasets"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--text-subtle)'
    }
  }, "/"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      fontSize: 14
    }
  }, "hey-atlas / prod"), /*#__PURE__*/React.createElement(Badge, {
    tone: "brand"
  }, "128 new"), /*#__PURE__*/React.createElement(ToolbarSeparator, null), /*#__PURE__*/React.createElement(Input, {
    size: "sm",
    placeholder: "Filter by device, time, confidence\u2026",
    style: {
      width: 260
    },
    prefix: /*#__PURE__*/React.createElement(Ico, {
      d: "M7 2a5 5 0 100 10 5 5 0 000-10zM11.5 11.5L14 14",
      size: 12
    })
  }), /*#__PURE__*/React.createElement(ToolbarSpacer, null), /*#__PURE__*/React.createElement(Switch, {
    checked: autoAdvance,
    onChange: setAutoAdvance,
    label: "Auto-advance"
  }), /*#__PURE__*/React.createElement(ToolbarSeparator, null), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "ghost"
  }, "Export"), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "primary"
  }, "Save labels (", counts.labeled, ")")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 320,
      minWidth: 320,
      borderRight: '1px solid var(--border-subtle)',
      background: 'var(--surface-panel)',
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 12px',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    value: tab,
    onChange: setTab,
    tabs: [{
      value: 'unlabeled',
      label: 'Unlabeled',
      count: counts.unlabeled
    }, {
      value: 'labeled',
      label: 'Labeled',
      count: counts.labeled
    }, {
      value: 'flagged',
      label: 'Flagged',
      count: 8
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto'
    }
  }, clips.map((c, i) => {
    const active = i === selIdx;
    const tone = c.label ? WAKE_LABELS.find(l => l.id === c.label)?.tone : null;
    const toneColor = tone ? `var(--${tone === 'bgnoise' ? 'bg' : tone}-500)` : 'transparent';
    return /*#__PURE__*/React.createElement("button", {
      key: c.id,
      onClick: () => {
        setSelIdx(i);
        setPlayhead(0);
      },
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        width: '100%',
        padding: '10px 12px',
        border: 'none',
        textAlign: 'left',
        background: active ? 'var(--accent-quiet)' : 'transparent',
        borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
        borderBottom: '1px solid var(--border-subtle)',
        cursor: 'pointer',
        color: 'var(--text-body)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 3,
        alignSelf: 'stretch',
        background: toneColor,
        borderRadius: 2
      }
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 4
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        color: 'var(--text-body)',
        fontWeight: 500
      }
    }, c.id), c.label && /*#__PURE__*/React.createElement(Badge, {
      tone: c.label === 'bgnoise' ? 'bgnoise' : c.label,
      style: {
        height: 16,
        padding: '0 6px',
        fontSize: 9
      }
    }, WAKE_LABELS.find(l => l.id === c.label).short)), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 10,
        fontSize: 11,
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-mono)'
      }
    }, /*#__PURE__*/React.createElement("span", null, c.duration, "s"), /*#__PURE__*/React.createElement("span", null, "\xB7"), /*#__PURE__*/React.createElement("span", null, c.device), /*#__PURE__*/React.createElement("span", null, "\xB7"), /*#__PURE__*/React.createElement("span", null, "conf ", c.confidence))));
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: 20,
      overflow: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(Card, {
    padded: false
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '14px 18px',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 16,
      fontWeight: 600
    }
  }, clip.id), /*#__PURE__*/React.createElement(Badge, {
    mono: true
  }, clip.duration, "s"), /*#__PURE__*/React.createElement(Badge, {
    tone: "brand"
  }, "conf ", clip.confidence)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)'
    }
  }, clip.device, " \xB7 captured today at ", clip.time)), /*#__PURE__*/React.createElement(IconButton, {
    "aria-label": "Previous",
    onClick: () => setSelIdx(i => Math.max(0, i - 1))
  }, /*#__PURE__*/React.createElement(Ico, {
    d: "M10 3L5 8l5 5"
  })), /*#__PURE__*/React.createElement(IconButton, {
    "aria-label": "Next",
    onClick: () => setSelIdx(i => Math.min(clips.length - 1, i + 1))
  }, /*#__PURE__*/React.createElement(Ico, {
    d: "M6 3l5 5-5 5"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '22px 22px 14px'
    }
  }, /*#__PURE__*/React.createElement(Waveform, {
    seed: clip.seed,
    samples: 120,
    playhead: playhead,
    region: {
      start: .28,
      end: .44
    },
    onScrub: setPlayhead,
    height: 96
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      marginTop: 14
    }
  }, /*#__PURE__*/React.createElement(IconButton, {
    variant: "primary",
    size: "lg",
    "aria-label": playing ? 'Pause' : 'Play',
    onClick: () => setPlaying(p => !p)
  }, playing ? /*#__PURE__*/React.createElement(PauseIcon, null) : /*#__PURE__*/React.createElement(PlayIcon, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      color: 'var(--text-muted)'
    }
  }, (playhead * parseFloat(clip.duration)).toFixed(2), "s / ", clip.duration, "s"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: 'auto',
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 12,
      color: 'var(--text-muted)'
    }
  }, /*#__PURE__*/React.createElement(Kbd, null, "Space"), " play", /*#__PURE__*/React.createElement(Kbd, null, "J"), "/", /*#__PURE__*/React.createElement(Kbd, null, "K"), " nav"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '16px 22px',
      borderTop: '1px solid var(--border-subtle)',
      background: 'var(--surface-sunken)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      textTransform: 'uppercase',
      letterSpacing: 'var(--tracking-caps)',
      color: 'var(--text-subtle)',
      fontWeight: 600,
      marginBottom: 10
    }
  }, "Label this clip"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      flexWrap: 'wrap'
    }
  }, WAKE_LABELS.map(l => /*#__PURE__*/React.createElement(LabelChip, {
    key: l.id,
    tone: l.tone,
    shortcut: l.key,
    selected: clip.label === l.id,
    onClick: () => setLabel(l.id)
  }, l.label))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Clip metadata",
    elevation: "flat"
  }, /*#__PURE__*/React.createElement(KeyValue, {
    items: [{
      k: 'Clip ID',
      v: clip.id,
      mono: true
    }, {
      k: 'Duration',
      v: `${clip.duration}s`,
      mono: true
    }, {
      k: 'Sample rate',
      v: '16 kHz',
      mono: true
    }, {
      k: 'Device',
      v: clip.device
    }, {
      k: 'Model version',
      v: 'wake-atlas-v3.2.1',
      mono: true
    }, {
      k: 'Confidence',
      v: clip.confidence,
      mono: true
    }]
  })), /*#__PURE__*/React.createElement(Card, {
    title: "Session progress"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(StatCell, {
    label: "Labeled",
    value: counts.labeled,
    unit: `/ ${clips.length}`
  }), /*#__PURE__*/React.createElement(StatCell, {
    label: "Session accuracy",
    value: "94.2%",
    delta: "vs last: +1.1%",
    deltaTone: "up"
  }), /*#__PURE__*/React.createElement(StatCell, {
    label: "Median time",
    value: "3.4s",
    unit: "per clip"
  }), /*#__PURE__*/React.createElement(StatCell, {
    label: "Flagged",
    value: counts.flagged,
    deltaTone: "neutral"
  }))))))));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(Annotator, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/wake_word/Annotator.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Card = __ds_scope.Card;

__ds_ns.KeyValue = __ds_scope.KeyValue;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.ConversationTurn = __ds_scope.ConversationTurn;

__ds_ns.Kbd = __ds_scope.Kbd;

__ds_ns.StatCell = __ds_scope.StatCell;

__ds_ns.ToolInvocation = __ds_scope.ToolInvocation;

__ds_ns.Waveform = __ds_scope.Waveform;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.WAKE_LABELS = __ds_scope.WAKE_LABELS;

__ds_ns.LabelChip = __ds_scope.LabelChip;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.RadioGroup = __ds_scope.RadioGroup;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Textarea = __ds_scope.Textarea;

__ds_ns.Sidebar = __ds_scope.Sidebar;

__ds_ns.SidebarSection = __ds_scope.SidebarSection;

__ds_ns.SidebarItem = __ds_scope.SidebarItem;

__ds_ns.Toolbar = __ds_scope.Toolbar;

__ds_ns.ToolbarSeparator = __ds_scope.ToolbarSeparator;

__ds_ns.ToolbarSpacer = __ds_scope.ToolbarSpacer;

})();
