export const formatTime = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

export const formatDateTime = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
};

export const formatSeconds = (value) =>
  typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(2)}s` : "—";

export const formatConfidence = (value) =>
  typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "—";

export const formatRate = (value) =>
  typeof value === "number" && value > 0 ? `${(value / 1000).toFixed(value % 1000 ? 1 : 0)} kHz` : "—";

export const shortId = (value, length = 10) => {
  if (!value) return "—";
  const text = String(value);
  return text.length <= length ? text : `${text.slice(0, length)}…`;
};

/** Pretty-print JSON, passing through text that is not valid JSON. */
export const toJsonText = (value) => {
  if (value == null) return "{}";
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};
