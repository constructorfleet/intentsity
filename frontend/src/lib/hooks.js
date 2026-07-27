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

/**
 * Track the rendered width of an element. The panel shares the page with Home
 * Assistant's own sidebar, so the viewport is a poor proxy for the space the
 * screen actually has: breakpoints read from the container instead.
 */
export function useElementWidth(ref) {
  const [width, setWidth] = React.useState(0);

  React.useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    if (typeof ResizeObserver === "undefined") {
      setWidth(node.getBoundingClientRect().width);
      return undefined;
    }
    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.round(entry.contentRect.width));
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [ref]);

  return width;
}

const readStoredWidth = (key, fallback) => {
  try {
    const stored = Number(window.localStorage.getItem(key));
    return Number.isFinite(stored) && stored > 0 ? stored : fallback;
  } catch {
    return fallback;
  }
};

/**
 * A column the reviewer can drag to resize, remembered across sessions.
 *
 * `edge` says which side of the column the handle sits on: a handle to the
 * right of its column grows it as the pointer moves right ("start"), one to the
 * left grows it as the pointer moves left ("end").
 *
 * Returns props to spread onto a `<Resizer>`, plus the current width. Arrow keys
 * nudge the divider and Home resets it, so the layout is not mouse-only.
 */
export function useResizableColumn(storageKey, { initial, min = 200, max = 640, edge = "start" }) {
  const [width, setWidthState] = React.useState(() => readStoredWidth(storageKey, initial));
  const [dragging, setDragging] = React.useState(false);

  const setWidth = React.useCallback(
    (value) => {
      const next = Math.round(Math.min(max, Math.max(min, value)));
      setWidthState(next);
      try {
        window.localStorage.setItem(storageKey, String(next));
      } catch {
        // Private browsing: an unsaved preference is not worth failing over.
      }
      return next;
    },
    [max, min, storageKey],
  );

  const widthRef = React.useRef(width);
  widthRef.current = width;

  const onPointerDown = React.useCallback(
    (event) => {
      if (event.button != null && event.button !== 0) return;
      event.preventDefault();
      const handle = event.currentTarget;
      const startX = event.clientX;
      const startWidth = widthRef.current;
      const direction = edge === "end" ? -1 : 1;

      // Capture keeps the move stream on the handle even when the pointer runs
      // ahead of the divider, which also means it works inside the shadow root.
      handle.setPointerCapture?.(event.pointerId);
      setDragging(true);
      // The panel's stylesheet lives in a shadow root and cannot reach the
      // document, so the drag cursor and selection lock go on directly.
      const restore = {
        cursor: document.body.style.cursor,
        userSelect: document.body.style.userSelect,
      };
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      const move = (moveEvent) => {
        setWidth(startWidth + (moveEvent.clientX - startX) * direction);
      };
      const stop = () => {
        setDragging(false);
        document.body.style.cursor = restore.cursor;
        document.body.style.userSelect = restore.userSelect;
        handle.releasePointerCapture?.(event.pointerId);
        handle.removeEventListener("pointermove", move);
        handle.removeEventListener("pointerup", stop);
        handle.removeEventListener("pointercancel", stop);
      };

      handle.addEventListener("pointermove", move);
      handle.addEventListener("pointerup", stop);
      handle.addEventListener("pointercancel", stop);
    },
    [edge, setWidth],
  );

  const onKeyDown = React.useCallback(
    (event) => {
      const direction = edge === "end" ? -1 : 1;
      const step = event.shiftKey ? 48 : 12;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        setWidth(widthRef.current - step * direction);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        setWidth(widthRef.current + step * direction);
      } else if (event.key === "Home") {
        event.preventDefault();
        setWidth(initial);
      }
    },
    [edge, initial, setWidth],
  );

  const reset = React.useCallback(() => setWidth(initial), [initial, setWidth]);

  return {
    width,
    dragging,
    handleProps: {
      dragging,
      onPointerDown,
      onKeyDown,
      onDoubleClick: reset,
      "aria-valuenow": width,
      "aria-valuemin": min,
      "aria-valuemax": max,
    },
  };
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
