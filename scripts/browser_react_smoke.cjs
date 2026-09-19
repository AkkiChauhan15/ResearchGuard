/* PLAYWRIGHT_PATH can point to an existing playwright-core installation. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright-core');
const frontendUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:5173';
const screenshotDir = process.env.SCREENSHOT_DIR || 'test-results';

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    let expectingApiFailure = false;
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error' && !expectingApiFailure) errors.push(`Console: ${message.text()}`);
    });
    page.on('requestfailed', (request) => {
      if (!request.url().includes('/api/reviews/demo')) {
        errors.push(`Request failed: ${request.url()} ${request.failure()?.errorText || ''}`);
      }
    });

    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Check the evidence. Keep the qualifications.' }).waitFor();
    await page.getByText('Live model service unavailable.', { exact: false }).waitFor();
    await page.getByText('You are signed out.', { exact: false }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Sign in with Google' }).isDisabled(), true);
    assert.equal(await page.getByText('A claim is a starting point.', { exact: true }).count(), 1);

    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.textContent), 'Skip to review');
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'main-content');
    await page.getByLabel('Answer or claim to review').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'intended-use');

    await fs.mkdir(screenshotDir, { recursive: true });
    await page.screenshot({ path: `${screenshotDir}/react-empty-desktop.png`, fullPage: true });

    await page.getByRole('button', { name: 'Open demonstration' }).click();
    await page.getByText('Demonstration — not a live verification', { exact: true }).waitFor();
    await page.getByRole('heading', { name: 'What the retrieved material shows' }).waitFor();
    await page.getByText('Partial result or access limitation', { exact: true }).waitFor();
    assert.ok(await page.getByText('abstract access', { exact: true }).count());
    assert.ok(await page.getByText('product document access', { exact: true }).count());
    assert.ok(await page.getByText('Next verification question', { exact: true }).count());
    assert.ok(await page.getByText('Access limitations', { exact: true }).count());

    await page.getByLabel('Your final wording').fill('Synthetic review: puncta count alone does not resolve autophagic flux.');
    await page.getByLabel('Researcher notes').fill('Checked that the accessible paper material is abstract only.');
    await page.getByRole('button', { name: 'Save edited wording' }).click();
    await page.getByText('Researcher decision: edited', { exact: true }).waitFor();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Export JSON' }).click();
    const download = await downloadPromise;
    const downloadPath = await download.path();
    const exported = JSON.parse(await fs.readFile(downloadPath, 'utf8'));
    assert.equal(exported.mode, 'demo');
    assert.equal(exported.claims[0].decision.status, 'edited');
    assert.equal(exported.claims[0].decision.notes, 'Checked that the accessible paper material is abstract only.');
    assert.equal(exported.sources.length, 2);
    await fs.copyFile(downloadPath, `${screenshotDir}/autophagy-demo-export.json`);
    await fs.writeFile(
      `${screenshotDir}/browser-run.json`,
      `${JSON.stringify({
        captured_at: new Date().toISOString(),
        application_url: frontendUrl,
        journey: 'public demonstration without authentication',
        input_origin: 'reconstructed synthetic input shown by the curated demonstration',
        model_output: null,
        model_status: 'not called; curated demonstration only',
        researcher_edit_preserved: true,
        exported_review_created_at: exported.created_at,
      }, null, 2)}\n`,
    );
    await page.screenshot({ path: `${screenshotDir}/react-demo-desktop.png`, fullPage: true });

    await page.getByLabel('Answer or claim to review').fill('A synthetic observation proves that cellular activity increased.');
    assert.equal(await page.getByRole('button', { name: 'Start live review' }).isDisabled(), true);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: `${screenshotDir}/react-signed-out-mobile.png`, fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
    const bodyFontSize = await page.evaluate(() => Number.parseFloat(getComputedStyle(document.body).fontSize));
    assert.ok(bodyFontSize >= 16);

    expectingApiFailure = true;
    await page.route('**/api/reviews/demo', (route) => route.abort('failed'));
    await page.getByRole('button', { name: 'Open demonstration' }).click();
    await page.getByRole('alert').waitFor();
    await page.getByText('The local backend is unavailable.', { exact: false }).waitFor();
    assert.equal(await page.getByText('Demonstration — not a live verification', { exact: true }).count(), 1);
    assert.equal(await page.getByText('Researcher decision: edited', { exact: true }).count(), 1);
    await page.unroute('**/api/reviews/demo');
    expectingApiFailure = false;

    assert.deepEqual(errors, []);
    console.log('React browser smoke passed: logged-out state, public demo evidence/access, edited decision/export, disabled live request, failed API state, safe mobile layout; no page errors.');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
