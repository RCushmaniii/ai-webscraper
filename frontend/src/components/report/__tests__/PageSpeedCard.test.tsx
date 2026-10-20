import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { describe, expect, it } from "vitest";
import PageSpeedCard from "../PageSpeedCard";
import type { PageSpeedData } from "../../../services/api";

const data: PageSpeedData = {
  source: "Google PageSpeed Insights (Lighthouse)",
  fetched_at: "2026-10-20T16:00:00+00:00",
  keyed: true,
  results: [
    {
      url: "https://www.cushlabs.ai/",
      strategy: "mobile",
      performance_score: 97,
      lcp_ms: 1240,
      cls: 0.012,
      tbt_ms: 30,
      fcp_ms: 912,
      server_response_ms: 210,
      field: { overall_category: "FAST", lcp_ms: 1800, inp_ms: 120, cls: 0.02 },
    },
    {
      url: "https://www.cushlabs.ai/pricing/",
      strategy: "mobile",
      performance_score: 44,
      lcp_ms: 6100,
      cls: 0.31,
      tbt_ms: 900,
      field: null,
    },
  ],
  errors: ["mobile https://www.cushlabs.ai/broken/: HTTPStatusError"],
};

describe("PageSpeedCard", () => {
  it("renders nothing when there is no data", () => {
    const { container } = render(<PageSpeedCard pagespeed={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows each Lighthouse score with its vitals", () => {
    render(<PageSpeedCard pagespeed={data} />);
    expect(
      screen.getByText("Performance (Google PageSpeed Insights)"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Performance score 97 of 100"),
    ).toHaveTextContent("97");
    expect(
      screen.getByLabelText("Performance score 44 of 100"),
    ).toHaveTextContent("44");
    expect(screen.getByText("1.2 s")).toBeInTheDocument(); // LCP
    expect(screen.getByText("6.1 s")).toBeInTheDocument();
    expect(screen.getByText(/Real-user Chrome data/)).toHaveTextContent("fast");
    expect(screen.getByText(/could not be audited/)).toHaveTextContent(
      "1 page",
    );
  });
});
