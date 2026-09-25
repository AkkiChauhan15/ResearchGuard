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

    await page.route('**/auth/v1/settings', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          disable_signup: false,
          mailer_autoconfirm: false,
          external: { email: true, google: true },
        }),
      });
    });

    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Check the evidence. Keep the qualifications.' }).waitFor();
    assert.equal(await page.getByLabel('Review workflow').count(), 0);
    assert.equal(await page.getByLabel('Answer or claim to review').count(), 0);
    const signInButton = page.getByRole('button', { name: 'Sign in', exact: true });
    await signInButton.waitFor();

    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.textContent), 'Skip to content');
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'main-content');

    await fs.mkdir(screenshotDir, { recursive: true });
    await page.screenshot({ path: `${screenshotDir}/react-home-desktop.png`, fullPage: true });

    await page.getByRole('button', { name: 'About', exact: true }).click();
    await page.getByRole('heading', { name: 'Research support you can inspect.' }).waitFor();
    assert.equal(new URL(page.url()).pathname, '/about');
    assert.equal(await page.getByLabel('Review workflow').count(), 0);
    await page.getByRole('button', { name: 'Home', exact: true }).click();

    await page.goto(new URL('/dashboard', frontendUrl).toString(), { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Sign in to open your dashboard' }).waitFor();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.getByLabel('Review workflow').count(), 0);
    await page.goto(new URL('/chat', frontendUrl).toString(), { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Research assistant chat' }).waitFor();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.getByLabel('Review workflow').count(), 0);
    await page.getByRole('button', { name: 'Home', exact: true }).click();

    if (!(await signInButton.isDisabled())) {
      await signInButton.click();
      await page.getByRole('heading', { name: 'Welcome back' }).waitFor();
      await page.getByRole('button', { name: 'Continue with Google' }).waitFor();
      await page.getByLabel('Email address').waitFor();
      await page.getByLabel('Password').waitFor();
      await page.getByRole('button', { name: 'Forgot password?' }).click();
      await page.getByRole('heading', { name: 'Reset your password' }).waitFor();
      await page.goto(new URL('/update-password', frontendUrl).toString(), { waitUntil: 'networkidle' });
      await page.getByRole('heading', { name: 'Choose a new password' }).waitFor();
      await page.getByText('The recovery session is missing or expired.', { exact: false }).waitFor();
      await page.getByRole('button', { name: 'Request another recovery email' }).click();
      await page.getByRole('button', { name: 'Back to sign in' }).click();
      await page.getByRole('button', { name: 'Create an account' }).click();
      await page.getByRole('heading', { name: 'Create your Research Guard AI account' }).waitFor();
      await page.getByLabel('Full name').fill('Synthetic Researcher');
      await page.getByLabel('Email address').fill('researcher@example.test');
      await page.getByLabel('Password', { exact: true }).fill('test-password');
      await page.getByLabel('Confirm password').fill('different-password');
      await page.getByRole('button', { name: 'Create account' }).click();
      await page.getByRole('alert').getByText('The password and confirmation do not match.').waitFor();
      await page.screenshot({ path: `${screenshotDir}/react-signup-desktop.png`, fullPage: true });

      await page.setViewportSize({ width: 390, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
      await page.setViewportSize({ width: 1440, height: 1000 });

      await page.getByRole('button', { name: 'Explore the demo without signing in' }).click();
    } else {
      await page.getByRole('button', { name: 'Demo', exact: true }).click();
    }

    await page.getByText('Demonstration — not a live verification', { exact: true }).waitFor();
    assert.equal(new URL(page.url()).pathname, '/demo/cyto-id');
    assert.equal(await page.getByLabel('Review workflow').count(), 1);
    await page.getByRole('heading', { name: 'What the retrieved material shows' }).waitFor();
    await page.getByText('Partial result or access limitation', { exact: true }).waitFor();
    assert.ok(await page.getByText('abstract access', { exact: true }).count());
    assert.ok(await page.getByText('product document access', { exact: true }).count());
    assert.ok(await page.getByText('Next verification question', { exact: true }).count());
    assert.ok(await page.getByText('Access limitations', { exact: true }).count());
    assert.ok(await page.getByText('Integrity check unavailable — not confirmed clean', { exact: true }).count());
    assert.ok(await page.getByText('Integrity check not applicable to this source type', { exact: true }).count());

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

    const comparisonFixture = structuredClone(exported);
    const primaryAssessment = {
      assessment_id: 'assessment_browser_primary',
      provider: 'groq',
      model: 'fixture-primary',
      is_primary: true,
      label: 'insufficient',
      confidence: 'medium',
      quote_check_passed: true,
      source_ids: comparisonFixture.sources.map((source) => source.source_id),
      created_at: '2026-09-25T00:00:00+00:00',
      assessment: structuredClone(comparisonFixture.claims[0].assessment),
    };
    const secondAssessment = structuredClone(primaryAssessment);
    secondAssessment.assessment_id = 'assessment_browser_second';
    secondAssessment.provider = 'openrouter';
    secondAssessment.model = 'fixture-second';
    secondAssessment.is_primary = false;
    secondAssessment.assessment.explanation = 'Different fixture wording with the same structured comparison fields.';
    comparisonFixture.claims[0].provider_assessments = [primaryAssessment, secondAssessment];
    comparisonFixture.claims[0].second_opinion_attempts = [];
    await page.route('**/api/reviews/demo', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(comparisonFixture),
    }));
    await page.getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'Open the demo' }).click();
    await page.getByRole('heading', { name: 'Provider comparison' }).waitFor();
    assert.equal(await page.getByText('⚠ Providers disagree on', { exact: false }).count(), 0);

    comparisonFixture.claims[0].provider_assessments[1].label = 'uncertain';
    comparisonFixture.claims[0].provider_assessments[1].confidence = 'low';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByText('⚠ Providers disagree on label, confidence', { exact: true }).waitFor();
    await page.unroute('**/api/reviews/demo');

    await page.evaluate(() => {
      window.history.pushState({}, '', '/review/new');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
    await page.getByRole('heading', { name: 'What needs checking?' }).waitFor();
    assert.equal(await page.getByLabel('Review workflow').count(), 1);
    await page.getByLabel('Answer or claim to review').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'intended-use');
    await page.getByLabel('Answer or claim to review').fill('A synthetic observation proves that cellular activity increased.');
    assert.equal(await page.getByRole('button', { name: 'Start live review' }).isDisabled(), true);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: `${screenshotDir}/react-signed-out-mobile.png`, fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
    const bodyFontSize = await page.evaluate(() => Number.parseFloat(getComputedStyle(document.body).fontSize));
    assert.ok(bodyFontSize >= 16);

    expectingApiFailure = true;
    await page.route('**/api/reviews/demo', (route) => route.abort('failed'));
    await page.getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'Open the demo' }).click();
    await page.getByRole('alert').waitFor();
    await page.getByText('The backend service is unavailable.', { exact: false }).waitFor();
    assert.equal(await page.getByText('Demonstration — not a live verification', { exact: true }).count(), 1);
    assert.equal(await page.getByText('Researcher decision: edited', { exact: true }).count(), 1);
    await page.unroute('**/api/reviews/demo');
    expectingApiFailure = false;

    assert.deepEqual(errors, []);
    console.log('React browser smoke passed: routed home/about/dashboard/chat/new-review/demo surfaces, workflow-only step strip, login/signup/recovery UI, mismatch validation, logged-out public demo, evidence/access, structural provider comparison, edited decision/export, failed API state, safe mobile layout; no page errors.');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
