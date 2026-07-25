# Waveform

Bar-based waveform display. Pass real amplitude data via `bars` (0..1 floats) or omit for a deterministic preview from `seed`. `playhead` is 0..1; `region` highlights the wake-word span.

```jsx
<Waveform bars={amps} playhead={progress} region={{start:.3,end:.42}} onScrub={setProgress} />
```
