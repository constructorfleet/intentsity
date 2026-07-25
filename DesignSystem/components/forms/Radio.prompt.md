# Radio / RadioGroup

Single-select. Use for the annotation label picker in wake-word review.
```jsx
<RadioGroup>
  <Radio name="l" value="tp" checked={l==='tp'} onChange={()=>setL('tp')} label="True positive" />
  <Radio name="l" value="fp" checked={l==='fp'} onChange={()=>setL('fp')} label="False positive" />
</RadioGroup>
```
