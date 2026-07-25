# Dialog

Modal for confirmations, dataset creation, model deploy. Renders overlay + focus trap.
```jsx
<Dialog open={o} onClose={close} title="Discard labels?"
  footer={<><Button variant="ghost" onClick={close}>Cancel</Button><Button variant="danger" onClick={confirm}>Discard</Button></>}>
  You have 12 unsaved label changes.
</Dialog>
```
