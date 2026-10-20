import { describe, expect, it } from "vitest";
import {
  formatValidationErrors,
  getApiErrorMessage,
  labelForField,
} from "../apiError";

/** Minimal object axios.isAxiosError() accepts. */
function axiosErr(status: number | null, data?: unknown) {
  return {
    isAxiosError: true,
    message: status
      ? `Request failed with status code ${status}`
      : "Network Error",
    response: status ? { status, data } : undefined,
  };
}

const LABELS = { url: "Start URL", rate_limit: "Rate Limit" };

describe("labelForField", () => {
  it("uses the form label when one is known", () => {
    expect(labelForField(["body", "url"], LABELS)).toBe("Start URL");
  });
  it("prettifies unknown keys", () => {
    expect(labelForField(["body", "max_pages"], {})).toBe("Max pages");
  });
  it("returns null for a bare location", () => {
    expect(labelForField(["body"], {})).toBeNull();
    expect(labelForField(undefined, {})).toBeNull();
  });
});

describe("formatValidationErrors", () => {
  it("names the field and strips Pydantic's prefix", () => {
    const text = formatValidationErrors(
      [
        {
          loc: ["body", "url"],
          msg: "Value error, URL must start with http:// or https://",
        },
      ],
      LABELS,
    );
    expect(text).toBe("Start URL: URL must start with http:// or https://");
  });
  it("lists several errors", () => {
    const text = formatValidationErrors(
      [
        {
          loc: ["body", "rate_limit"],
          msg: "Input should be greater than or equal to 0.1",
        },
        {
          loc: ["body", "max_depth"],
          msg: "Input should be less than or equal to 10",
        },
      ],
      LABELS,
    );
    expect(text).toBe(
      "Rate Limit: Input should be greater than or equal to 0.1. Max depth: Input should be less than or equal to 10",
    );
  });
  it("returns null for garbage", () => {
    expect(formatValidationErrors([], {})).toBeNull();
  });
});

describe("getApiErrorMessage", () => {
  it("never surfaces the axios status-code string", () => {
    const text = getApiErrorMessage(axiosErr(422, { detail: [] }), "Fallback");
    expect(text).not.toMatch(/status code/i);
  });

  it("reads FastAPI validation errors with form labels", () => {
    const err = axiosErr(422, {
      detail: [
        {
          loc: ["body", "url"],
          msg: "Value error, URL must start with http:// or https://",
          type: "value_error",
        },
      ],
      message: "url: URL must start with http:// or https://",
    });
    expect(getApiErrorMessage(err, "Fallback", LABELS)).toBe(
      "Start URL: URL must start with http:// or https://",
    );
  });

  it("falls back to the server summary when the list is empty", () => {
    const err = axiosErr(422, {
      detail: [],
      message: "Request could not be validated",
    });
    expect(getApiErrorMessage(err, "Fallback")).toBe(
      "Request could not be validated",
    );
  });

  it("uses a string detail as written (route-level 422/403)", () => {
    const err = axiosErr(422, { detail: "User agent must identify a bot." });
    expect(getApiErrorMessage(err, "Fallback")).toBe(
      "User agent must identify a bot.",
    );
  });

  it("uses detail.message for structured errors", () => {
    const err = axiosErr(403, {
      detail: {
        error: "crawl_limit_reached",
        message: "Free tier limit reached.",
      },
    });
    expect(getApiErrorMessage(err, "Fallback")).toBe(
      "Free tier limit reached.",
    );
  });

  it("explains a network failure without the raw axios text", () => {
    expect(getApiErrorMessage(axiosErr(null), "Fallback")).toBe(
      "Could not reach the server. Check your connection and try again.",
    );
  });

  it("maps a 5xx to a calm sentence", () => {
    const text = getApiErrorMessage(
      axiosErr(502, "<html>Bad Gateway</html>"),
      "Fallback",
    );
    expect(text).toMatch(/our side/);
    expect(text).not.toMatch(/502/);
  });

  it("maps known 4xx codes and keeps the fallback for the rest", () => {
    expect(getApiErrorMessage(axiosErr(429, {}), "Fallback")).toMatch(
      /Too many requests/,
    );
    expect(getApiErrorMessage(axiosErr(418, {}), "Fallback")).toBe("Fallback");
  });

  it("handles blob bodies (file downloads) by status", () => {
    const err = axiosErr(404, new Blob(["x"]));
    expect(getApiErrorMessage(err, "Fallback")).toMatch(/no longer exists/);
  });

  it("returns the fallback for non-axios errors", () => {
    expect(
      getApiErrorMessage(new Error("TypeError: x is undefined"), "Fallback"),
    ).toBe("Fallback");
    expect(getApiErrorMessage(undefined, "Fallback")).toBe("Fallback");
  });
});
