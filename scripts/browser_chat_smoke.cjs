/* PLAYWRIGHT_PATH can point to an existing playwright-core installation. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright-core');

const frontendUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:5173';
const screenshotDir = process.env.SCREENSHOT_DIR || 'test-results/chat';

function readPublicSupabaseConfig() {
  const text = fs.readFileSync('frontend/.env.local', 'utf8');
  const values = Object.fromEntries(text.split(/\r?\n/).filter((line) => line && !line.startsWith('#')).map((line) => {
    const index = line.indexOf('=');
    return [line.slice(0, index), line.slice(index + 1)];
  }));
  const url = new URL(values.VITE_SUPABASE_URL);
  return { storageKey: `sb-${url.hostname.split('.')[0]}-auth-token` };
}

function fixtureToken(userId) {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
  return `${encode({ alg: 'ES256', typ: 'JWT', kid: 'fixture' })}.${encode({
    aud: 'authenticated',
    exp: Math.floor(Date.now() / 1000) + 3600,
    sub: userId,
    role: 'authenticated',
    email: 'chat@example.test',
  })}.fixture-signature`;
}

(async () => {
  const { storageKey } = readPublicSupabaseConfig();
  const userId = '00000000-0000-4000-8000-000000000020';
  const accessToken = fixtureToken(userId);
  const session = {
    access_token: accessToken,
    refresh_token: 'fixture-refresh-token',
    expires_in: 3600,
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    token_type: 'bearer',
    user: {
      id: userId,
      aud: 'authenticated',
      role: 'authenticated',
      email: 'chat@example.test',
      app_metadata: { provider: 'google', providers: ['google'] },
      user_metadata: {},
      identities: [],
      created_at: new Date().toISOString(),
    },
  };

  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errors = [];
    const requests = [];
    let failNextChat = false;
    let expectingApiFailure = false;
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error' && !expectingApiFailure) errors.push(`Console: ${message.text()}`);
    });
    await page.addInitScript(({ key, value }) => localStorage.setItem(key, JSON.stringify(value)), {
      key: storageKey,
      value: session,
    });

    await page.route('**/api/config', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        model_configured: true,
        model_state: 'configured',
        model_provider: 'gemini',
        extraction_model: 'gemini-3.8-flash',
        assessment_model: 'gemini-3.8-flash',
        model_detail: 'Fixture',
        retention_seconds: 3600,
        mode: 'local preview',
        auth_configured: true,
        auth_state: 'configured',
        auth_provider: 'supabase_google',
        live_auth_required: true,
        persistence_configured: false,
        persistence_state: 'unavailable_missing_configuration',
      }),
    }));
    await page.route('**/api/auth/me', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ user_id: userId, email: 'chat@example.test' }),
    }));
    await page.route('**/api/chat/providers', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        config_version: 'browser-fixture',
        fallback_enabled: true,
        providers: [
          { id: 'groq', display_name: 'Groq', configured: false, state: 'missing_api_key', models: [{ id: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant' }] },
          { id: 'openrouter', display_name: 'OpenRouter', configured: true, state: 'configured', models: [{ id: 'openrouter/free', label: 'OpenRouter Free Router' }] },
          { id: 'gemini', display_name: 'Google Gemini', configured: true, state: 'configured', models: [{ id: 'gemini-3.8-flash', label: 'Gemini 3.8 Flash' }] },
          { id: 'nvidia', display_name: 'NVIDIA NIM', configured: false, state: 'free_tier_unconfirmed', models: [{ id: 'meta/llama-3.1-8b-instruct', label: 'Llama 3.1 8B Instruct' }] },
        ],
      }),
    }));
    await page.route('**/api/chat', async (route) => {
      const body = route.request().postDataJSON();
      requests.push(body);
      if (failNextChat) {
        failNextChat = false;
        await route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ error: 'Fixture free quota is exhausted. Retry later.' }) });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          provider: body.provider,
          requested_provider: body.provider,
          model: body.model,
          requested_model: body.model,
          answer: requests.length === 1
            ? 'MELAS is a mitochondrial disorder.'
            : requests.length === 2
              ? 'A common cause is the m.3243A>G variant.'
              : 'Conversation continued after the failed call.',
          fallback_used: false,
          attempts: [{ provider: body.provider, model: body.model, status: 'success' }],
        }),
      });
    });

    await page.goto(new URL('/chat', frontendUrl).toString(), { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Research assistant chat' }).waitFor();
    await page.getByText('These replies are model output and are not evidence-checked.', { exact: false }).waitFor();
    await page.getByLabel('AI provider').selectOption('openrouter');
    assert.equal(await page.getByLabel('Model', { exact: true }).inputValue(), 'openrouter/free');
    await page.getByLabel('Message').fill('What is MELAS?');
    await page.getByLabel('Message').press('Enter');
    await page.getByText('MELAS is a mitochondrial disorder.', { exact: true }).waitFor();
    await page.getByText('Generated by openrouter · openrouter/free · not evidence-checked', { exact: true }).waitFor();

    await page.getByLabel('Message').fill('What mutation commonly causes it?');
    await page.getByRole('button', { name: 'Send', exact: true }).click();
    await page.getByText('A common cause is the m.3243A>G variant.', { exact: true }).waitFor();
    assert.equal(requests.length, 2);
    assert.deepEqual(requests[1].messages.map((item) => item.role), ['user', 'assistant', 'user']);
    assert.equal(requests[1].messages[1].content, 'MELAS is a mitochondrial disorder.');

    failNextChat = true;
    expectingApiFailure = true;
    await page.getByLabel('Message').fill('Trigger a bounded fixture error.');
    await page.getByRole('button', { name: 'Send', exact: true }).click();
    await page.getByRole('alert').getByText('Fixture free quota is exhausted.', { exact: false }).waitFor();
    expectingApiFailure = false;
    assert.equal(await page.getByText('Trigger a bounded fixture error.', { exact: true }).count(), 1);
    await page.getByText('Request failed; this message will not be included in later model context.', { exact: true }).waitFor();
    await page.getByLabel('Message').fill('Continue with the last successful context.');
    await page.getByRole('button', { name: 'Send', exact: true }).click();
    await page.getByText('Conversation continued after the failed call.', { exact: true }).waitFor();
    assert.equal(requests[3].messages.some((item) => item.content === 'Trigger a bounded fixture error.'), false);
    assert.equal(requests[3].messages.at(-1).content, 'Continue with the last successful context.');

    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
    await fsp.mkdir(screenshotDir, { recursive: true });
    await page.screenshot({ path: `${screenshotDir}/chat-mobile.png`, fullPage: true });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.getByRole('button', { name: 'Clear chat' }).click();
    await page.getByRole('heading', { name: 'What would you like to understand?' }).waitFor();
    await page.screenshot({ path: `${screenshotDir}/chat-empty-desktop.png`, fullPage: true });

    assert.deepEqual(errors, []);
    console.log('Chat browser smoke passed: signed-in route, provider/model selection, two-turn context, normalized metadata, error retention/exclusion from later context, clear action, and 390 px layout.');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
