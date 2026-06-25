// Captures screenshots of every screen against a running `next start` server and writes
// them to docs/screenshots/. Usage: node frontend/scripts/capture-screenshots.mjs
// (start the server first: PORT=3100 npm --prefix frontend run start). Override the base
// URL with SHOT_BASE. Requires the playwright devDependency + `playwright install chromium`.

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const BASE = process.env.SHOT_BASE ?? "http://localhost:3100";
// frontend/scripts → repo-root/docs/screenshots, independent of cwd
const OUT = path.resolve(import.meta.dirname, "..", "..", "docs", "screenshots");

// [route, output file, fullPage]
const SHOTS = [
  ["/", "landing.png", true],
  ["/dashboard", "dashboard.png", false],
  ["/pulls", "pulls.png", false],
  ["/pulls/142", "pr-analysis.png", false],
  ["/reviews/rev_1000", "review-results.png", false],
  ["/agent", "agent.png", false],
  ["/knowledge", "knowledge.png", false],
  ["/costs", "costs.png", false],
  ["/history", "history.png", false],
  ["/settings", "settings.png", false],
];

async function gotoWithRetry(page, url, tries = 30) {
  for (let i = 0; i < tries; i++) {
    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: 15000 });
      return;
    } catch (err) {
      if (i === tries - 1) throw err;
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    colorScheme: "dark",
  });
  const page = await ctx.newPage();

  for (const [route, file, fullPage] of SHOTS) {
    await gotoWithRetry(page, BASE + route);
    await page.waitForTimeout(2000); // let client fetches + charts/graph settle
    await page.screenshot({ path: path.join(OUT, file), fullPage });
    console.log("captured", file);
  }

  // One mobile shot for the responsive dashboard.
  const mobile = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    colorScheme: "dark",
  });
  const mpage = await mobile.newPage();
  await gotoWithRetry(mpage, BASE + "/dashboard");
  await mpage.waitForTimeout(2000);
  await mpage.screenshot({ path: path.join(OUT, "mobile-dashboard.png"), fullPage: false });
  console.log("captured mobile-dashboard.png");

  await browser.close();
  console.log("done →", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
