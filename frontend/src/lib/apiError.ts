/**
 * Turn any failed API call into one sentence a person can act on.
 *
 * Why: on 2026-10-19 a crawl submission was refused with a 422 and the toast
 * read "Request failed with status code 422", axios's fallback text. Nothing
 * on the client knew how to read FastAPI's validation payload, so the user
 * saw a status code and the field that was wrong stayed a mystery.
 *
 * The backend contract this reads (backend/app/core/errors.py):
 *   422  { detail: [{ loc, msg, type }], message: "url: URL must start ..." }
 *   4xx  { detail: "plain sentence" } or { detail: { message: "...", ... } }
 *   429  { detail: "...", retry_after: 60 }
 *   5xx  { detail: "Something went wrong on our side. ...", error_id: "3f9a1c2e" }
 *
 * Rules:
 *  - Never show an axios/network error message verbatim.
 *  - Never show a raw status code to the user.
 *  - Prefer the server's own sentence when it wrote one for people.
 */

import { isAxiosError } from "axios";

export type FieldLabels = Record<string, string>;

interface ValidationItem {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
}

const LOCATION_PREFIXES = new Set([
  "body",
  "query",
  "path",
  "header",
  "cookie",
]);
const VALUE_ERROR_PREFIX = "Value error, ";

const STATUS_MESSAGES: Record<number, string> = {
  400: "The request was not understood. Please check the form and try again.",
  401: "Your session has expired. Please sign in again.",
  403: "You don't have permission to do that.",
  404: "That item no longer exists. It may have been deleted.",
  408: "The server took too long to respond. Please try again.",
  409: "That conflicts with something that already exists.",
  413: "That request is too large to send.",
  429: "Too many requests. Please wait a moment and try again.",
};

const SERVER_ERROR_MESSAGE =
  "Something went wrong on our side. It has been logged; please try again in a moment.";
const NETWORK_ERROR_MESSAGE =
  "Could not reach the server. Check your connection and try again.";

/** "max_pages" -> "Max pages" unless a label is supplied. */
export function labelForField(
  loc: Array<string | number> | undefined,
  labels: FieldLabels,
): string | null {
  if (!loc || loc.length === 0) return null;
  const parts = loc.map(String);
  const path =
    parts.length > 1 && LOCATION_PREFIXES.has(parts[0])
      ? parts.slice(1)
      : parts;
  if (path.length === 0) return null;
  // ("body", 30) is a byte offset for malformed JSON, not a field.
  if (path.every((p) => /^\d+$/.test(p))) return null;
  const key = path.join(".");
  if (labels[key]) return labels[key];
  if (path.length === 1 && LOCATION_PREFIXES.has(path[0])) return null; // bare "body"
  const pretty = key.replace(/[_.]/g, " ").trim();
  return pretty.charAt(0).toUpperCase() + pretty.slice(1);
}

function cleanMessage(msg: string | undefined): string {
  const text = (msg || "").trim();
  if (!text) return "is invalid";
  return text.startsWith(VALUE_ERROR_PREFIX)
    ? text.slice(VALUE_ERROR_PREFIX.length)
    : text;
}

/** FastAPI/Pydantic error list -> "Start URL: URL must start with http:// or https://". */
export function formatValidationErrors(
  items: ValidationItem[],
  labels: FieldLabels = {},
): string | null {
  const sentences = items
    .filter((item) => item && typeof item === "object")
    .map((item) => {
      const label = labelForField(item.loc, labels);
      const reason = cleanMessage(item.msg);
      return label ? `${label}: ${reason}` : reason;
    })
    .filter(Boolean);
  if (sentences.length === 0) return null;
  // Repeating the same reason for several fields reads badly; dedupe.
  return Array.from(new Set(sentences)).join(". ");
}

function messageFromDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) return detail.trim();
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return message.trim();
  }
  return null;
}

/**
 * The sentence to show for a failed API call.
 *
 * @param err      whatever was caught
 * @param fallback what to say when the error carries nothing usable
 * @param labels   field key -> label as shown on the form, for 422s
 */
export function getApiErrorMessage(
  err: unknown,
  fallback: string,
  labels: FieldLabels = {},
): string {
  if (!isAxiosError(err)) return fallback;

  const response = err.response;
  if (!response) return NETWORK_ERROR_MESSAGE;

  const status = response.status;
  const data: unknown = response.data;
  const body =
    data && typeof data === "object" && !(data instanceof Blob)
      ? (data as Record<string, unknown>)
      : null;

  // A 5xx body is never shown, whatever it says. On 2026-10-20 one read
  // "An unexpected error occurred: {'message': 'invalid input syntax for
  // type integer: \"1.0\"', 'code': '22P02', ...}" straight from Postgres.
  // The server logs the cause under error_id; showing the id lets the
  // person quote it instead of describing the toast.
  if (status >= 500) {
    const errorId =
      body && typeof body.error_id === "string" ? body.error_id.trim() : "";
    return errorId
      ? `${SERVER_ERROR_MESSAGE} Reference: ${errorId}.`
      : SERVER_ERROR_MESSAGE;
  }

  if (body) {
    if (status === 422 && Array.isArray(body.detail)) {
      const formatted = formatValidationErrors(
        body.detail as ValidationItem[],
        labels,
      );
      if (formatted) return formatted;
    }
    const fromDetail = messageFromDetail(body.detail);
    if (fromDetail) return fromDetail;
    if (typeof body.message === "string" && body.message.trim())
      return body.message.trim();
  }

  return STATUS_MESSAGES[status] || fallback;
}
