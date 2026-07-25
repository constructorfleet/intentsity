# Select

Native `<select>` styled to match Input. Pass `options` as `{value,label}[]`.
```jsx
<Select value={model} onChange={e=>setModel(e.target.value)} options={[
  {value:'v1', label:'wake-model v1'}, {value:'v2', label:'wake-model v2'}
]} />
```
