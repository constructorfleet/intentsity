import React from "react";

/** Toast queue with automatic dismissal. */
export function useToasts(timeout = 4000) {
  const [toasts, setToasts] = React.useState([]);
  const nextId = React.useRef(0);

  const dismiss = React.useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = React.useCallback(
    (tone, title, description) => {
      const id = (nextId.current += 1);
      setToasts((current) => [...current, { id, tone, title, description }]);
      if (timeout > 0) {
        setTimeout(() => dismiss(id), timeout);
      }
      return id;
    },
    [dismiss, timeout],
  );

  return { toasts, push, dismiss };
}

/**
 * Subscribe to a websocket push channel, resubscribing when `filters` change.
 * `subscribe` must return a promise resolving to an unsubscribe function.
 */
export function useSubscription(subscribe, filters, handler, onError) {
  const filterKey = JSON.stringify(filters);
  const handlerRef = React.useRef(handler);
  handlerRef.current = handler;

  React.useEffect(() => {
    let unsubscribe;
    let cancelled = false;

    subscribe(JSON.parse(filterKey), (message) => handlerRef.current(message))
      .then((fn) => {
        // A resubscribe that lands after unmount must still be torn down.
        if (cancelled) fn();
        else unsubscribe = fn;
      })
      .catch((error) => onError?.(error));

    return () => {
      cancelled = true;
      unsubscribe?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey, subscribe]);
}

/** Window-level keydown handler that ignores events from text fields. */
export function useKeyboard(handler, enabled = true) {
  const handlerRef = React.useRef(handler);
  handlerRef.current = handler;

  React.useEffect(() => {
    if (!enabled) return undefined;
    const listener = (event) => {
      // The panel renders in a shadow root, so event.target is retargeted to
      // the host element; composedPath()[0] is the field the user is typing in.
      const origin = event.composedPath?.()[0] ?? event.target;
      const tag = origin?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (origin?.isContentEditable) return;
      handlerRef.current(event);
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [enabled]);
}
