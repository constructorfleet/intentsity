# LabelChip

The domain-specific chip for the five wake-word annotation classes. Use as a horizontal row on the review UI. Also export `WAKE_LABELS` for the canonical five-item list with keyboard shortcuts.

```jsx
{WAKE_LABELS.map(l => (
  <LabelChip key={l.id} tone={l.tone} shortcut={l.key}
    selected={sel===l.id} onClick={()=>setSel(l.id)}>{l.label}</LabelChip>
))}
```
