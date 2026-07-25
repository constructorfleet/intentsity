# Button

Standard action trigger. Use `primary` for the single strongest action on a view, `secondary` for peers, `ghost` inside dense toolbars, `danger` for destructive intents.

```jsx
<Button variant="primary" onClick={save}>Save labels</Button>
<Button variant="secondary" size="sm" iconLeft={<PlayIcon/>}>Play clip</Button>
<Button variant="danger" size="sm">Discard</Button>
```

Sizes: `sm` (dense toolbars), `md` (default), `lg` (marketing / hero CTAs — rare here).
Loading state disables the button and shows a spinner in place of `iconLeft`.
