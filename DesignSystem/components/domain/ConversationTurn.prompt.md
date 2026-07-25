# ConversationTurn

Renders a single role-tagged utterance in an intent-training transcript. Roles `user` (right-aligned, blue), `assistant` (left, panel), `tool` (left, mono, sunken), `system` (centered, muted).

```jsx
<ConversationTurn role="user" timestamp="0.4s">turn on the kitchen lights</ConversationTurn>
<ConversationTurn role="tool" name="lights.set">{"{ \"room\": \"kitchen\", \"on\": true }"}</ConversationTurn>
<ConversationTurn role="assistant">Turning on the kitchen lights.</ConversationTurn>
```
