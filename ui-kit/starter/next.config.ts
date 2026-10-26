import type { NextConfig } from "next";

// Mode A (static data): default build pre-renders the four nav surfaces;
// detail pages render on demand. Data is imported at build time from
// ./data/*.json (see lib/data.ts).
// Mode B (live localhost API): when/if you add the documented proxy route
// (app/api/forecasts/[...key]/route.ts), nothing here needs to change for
// `next build`; only for `output: "export"`-style pure-static hosting would
// the proxy route be impossible (API routes require the server).
const nextConfig: NextConfig = {};

export default nextConfig;
