import { execFileSync } from 'node:child_process';
import { randomBytes, randomInt } from 'node:crypto';
import { resolve } from 'node:path';
import type { Locator } from '@playwright/test';

import { test as base, expect } from '../test-with-coverage';
import { BLOG_ADMIN_EDIT, BLOG_ADMIN_DUPLICATE, BLOG_DETAIL, CAMPAIGN_DETAIL, CAMPAIGN_UPDATES_FEED } from '../helpers/flow-tags';

type Article = { id: number; slug: string; title_es: string; title_en: string };
type EditorialSession = {
  headers: { Authorization: string };
  createArticle: (data?: Record<string, unknown>) => Promise<Article>;
  trackCopy: (id: number) => void;
};

function requiredSetting(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing private editorial E2E setup: ${name}`);
  return value;
}

async function expectLoadedImage(image: Locator, source: string) {
  await expect(image).toBeVisible();
  await expect(image).toHaveAttribute('src', source);
  await expect.poll(() => image.evaluate((element) => (element as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
}

const test = base.extend<{ editorial: EditorialSession }>({
  editorial: async ({ page, context }, provide, testInfo) => {
    const email = requiredSetting('E2E_EDITORIAL_ADMIN_EMAIL');
    const password = requiredSetting('E2E_EDITORIAL_ADMIN_PASSWORD');
    // Each browser and its API requests share one real client identity.
    const clientIp = `2001:db8::${Array.from({ length: 4 }, () => randomInt(0x10000).toString(16)).join(':')}`;
    await context.setExtraHTTPHeaders({ 'X-Forwarded-For': clientIp });
    await page.goto('/es/sign-in?redirect=/admin/blog');
    await page.getByLabel('Correo electrónico').fill(email);
    await page.getByLabel('Contraseña', { exact: true }).fill(password);
    const login = page.waitForResponse((response) => response.url().endsWith('/auth/sign_in/')
      && response.request().method() === 'POST');
    await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
    const loginResponse = await login;
    expect(loginResponse.status()).toBe(200);
    const tokens = await loginResponse.json();
    expect(tokens.user.email).toBe(email);
    expect(tokens.user.is_staff).toBe(true);
    await expect(page).toHaveURL(/\/admin\/blog$/);
    const headers = { Authorization: `Bearer ${tokens.access}` };
    const createdIds: number[] = [];
    try {
      await provide({
        headers,
        createArticle: async (data = {}) => {
          const response = await context.request.post('/api/blog/admin/create/', {
            headers,
            data: {
              title_es: `Prueba editorial ${testInfo.parallelIndex}-${testInfo.retry}`,
              title_en: `Editorial proof ${testInfo.parallelIndex}-${testInfo.retry}`,
              excerpt_es: 'Resumen de prueba', excerpt_en: 'Test summary',
              content_es: '<p>Contenido de prueba</p>', content_en: '<p>Test content</p>',
              is_published: true, ...data,
            },
          });
          expect(response.status()).toBe(201);
          const article: Article = await response.json();
          createdIds.push(article.id);
          return article;
        },
        trackCopy: (id) => createdIds.push(id),
      });
    } finally {
      for (const id of createdIds) {
        const response = await context.request.delete(`/api/blog/admin/${id}/delete/`, { headers });
        expect(response.status()).toBe(204);
      }
    }
  },
});

test.beforeAll(() => {
  // CI owns an ephemeral migrated SQLite database. Local verification gets
  // an explicitly seeded private target from its coordinator instead.
  if (process.env.CI !== 'true') return;
  const backend = resolve(process.cwd(), '..', 'backend');
  const output = execFileSync(resolve(backend, 'venv', 'bin', 'python'), [
    '-c', [
      'import json, sys',
      'from pathlib import Path',
      "assert not (Path.cwd() / '.env').exists(), 'Editorial CI bootstrap refuses dotenv'",
      'sys.path.insert(0, str(Path.cwd()))',
      'import decouple',
      'decouple.config = decouple.Config(decouple.RepositoryEmpty())',
      'from django.conf import settings',
      'from huey import MemoryHuey',
      "settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'",
      "settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}",
      "settings.HUEY = MemoryHuey(name='editorial-r8-ci', immediate=True)",
      'import django',
      'django.setup()',
      'from base_feature_app.tests.e2e_editorial_seed import seed_editorial_e2e',
      "print('EDITORIAL_SEED=' + json.dumps(seed_editorial_e2e()))",
    ].join('\n'),
  ], {
    cwd: backend,
    env: {
      ...process.env, DJANGO_ENV: 'development',
      DJANGO_SETTINGS_MODULE: 'base_feature_project.settings_dev', E2E_EDITORIAL_SEED: '1',
      E2E_EDITORIAL_ADMIN_EMAIL: process.env.E2E_EDITORIAL_ADMIN_EMAIL || 'editorial-r8-ci@example.test',
      E2E_EDITORIAL_ADMIN_PASSWORD: process.env.E2E_EDITORIAL_ADMIN_PASSWORD || randomBytes(24).toString('base64url'),
    },
    encoding: 'utf8',
  });
  const marker = output.split('\n').find((line) => line.startsWith('EDITORIAL_SEED='));
  if (!marker) throw new Error('Private editorial CI seed did not return its fixture');
  const fixture: Record<string, string> = JSON.parse(marker.slice('EDITORIAL_SEED='.length));
  for (const [name, value] of Object.entries(fixture)) process.env[name] = String(value);
});

test('shows an uploaded cover after reloading the editor', {
  tag: [...BLOG_ADMIN_EDIT, ...BLOG_DETAIL, '@outcome:success'],
}, async ({ page, context, editorial }) => {
  const article = await editorial.createArticle();
  await page.goto('/es/admin/blog');
  await page.getByRole('row').filter({ has: page.getByText(article.slug, { exact: true }) })
    .getByRole('link', { name: 'Editar', exact: true }).click();
  await expect(page.getByLabel('Título (ES)', { exact: true })).toHaveValue(article.title_es);
  const uploaded = page.waitForResponse((response) => response.url().endsWith(`/blog/admin/${article.id}/upload-cover/`)
    && response.request().method() === 'POST');
  await page.getByLabel('Subir imagen', { exact: true }).setInputFiles({
    name: 'editorial-cover.png', mimeType: 'image/png',
    buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGNkYPjPwMDAxMDAwMDAAAALHwEDmIWXfgAAAABJRU5ErkJggg==', 'base64'),
  });
  const uploadedResponse = await uploaded;
  expect(uploadedResponse.status()).toBe(200);
  const post = await uploadedResponse.json();
  expect(typeof post.cover_image).toBe('number');
  await expectLoadedImage(page.getByAltText('Cover', { exact: true }), post.cover_image_display);
  await page.reload();
  await expectLoadedImage(page.getByAltText('Cover', { exact: true }), post.cover_image_display);

  const publicWindow = context.waitForEvent('page');
  await page.getByRole('link', { name: 'Ver en el blog →', exact: true }).click();
  const publicPage = await publicWindow;
  await expect(publicPage.getByRole('heading', { name: article.title_es, exact: true })).toBeVisible();
  await expectLoadedImage(publicPage.getByAltText(article.title_es, { exact: true }), post.cover_image_display);
  await publicPage.goto(`/en/blog/${article.slug}`);
  await expect(publicPage.getByRole('heading', { name: article.title_en, exact: true })).toBeVisible();
  await expectLoadedImage(publicPage.getByAltText(article.title_en, { exact: true }), post.cover_image_display);
});

test('preserves editorial metadata when duplicating an article', {
  tag: [...BLOG_ADMIN_DUPLICATE, ...BLOG_ADMIN_EDIT, '@outcome:success'],
}, async ({ page, editorial }) => {
  const metadata = {
    author: 'laura-blanco', cover_image_credit: 'Editorial photographer',
    cover_image_credit_url: 'https://example.test/editorial-photographer',
    meta_keywords_es: 'adopción,perros', meta_keywords_en: 'adoption,dogs', is_featured: true,
  };
  const article = await editorial.createArticle(metadata);
  await page.goto('/es/admin/blog');
  await page.getByRole('row').filter({ has: page.getByText(article.slug, { exact: true }) })
    .getByRole('button', { name: 'Duplicar', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Duplicar post', exact: true });
  const duplicated = page.waitForResponse((response) => response.url().endsWith(`/blog/admin/${article.id}/duplicate/`)
    && response.request().method() === 'POST');
  await dialog.getByRole('button', { name: 'Duplicar', exact: true }).click();
  const duplicatedResponse = await duplicated;
  expect(duplicatedResponse.status()).toBe(201);
  const copy = await duplicatedResponse.json();
  editorial.trackCopy(copy.id);
  expect(copy.slug).not.toBe(article.slug);
  expect(copy.is_published).toBe(false);
  expect(copy.published_at).toBeNull();
  expect(copy.is_featured).toBe(false);
  await page.getByRole('row').filter({ has: page.getByText(copy.slug, { exact: true }) })
    .getByRole('link', { name: 'Editar', exact: true }).click();
  await expect(page.getByLabel('Autor', { exact: true })).toHaveValue(metadata.author);
  await expect(page.getByLabel('Crédito', { exact: true })).toHaveValue(metadata.cover_image_credit);
  await expect(page.getByLabel('URL crédito', { exact: true })).toHaveValue(metadata.cover_image_credit_url);
  await expect(page.getByLabel('Keywords (ES)', { exact: true })).toHaveValue(metadata.meta_keywords_es);
  await expect(page.getByLabel('Keywords (EN)', { exact: true })).toHaveValue(metadata.meta_keywords_en);
  await page.reload();
  await expect(page.getByLabel('Autor', { exact: true })).toHaveValue(metadata.author);
  await expect(page.getByLabel('Crédito', { exact: true })).toHaveValue(metadata.cover_image_credit);
  await expect(page.getByLabel('URL crédito', { exact: true })).toHaveValue(metadata.cover_image_credit_url);
  await expect(page.getByLabel('Keywords (ES)', { exact: true })).toHaveValue(metadata.meta_keywords_es);
  await expect(page.getByLabel('Keywords (EN)', { exact: true })).toHaveValue(metadata.meta_keywords_en);
});

test('loads the illustrated update in a completed campaign', {
  tag: [...CAMPAIGN_DETAIL, ...CAMPAIGN_UPDATES_FEED, '@outcome:display'],
}, async ({ page, context, editorial }) => {
  const campaignId = requiredSetting('E2E_EDITORIAL_CAMPAIGN_ID');
  const updateId = requiredSetting('E2E_EDITORIAL_UPDATE_ID');
  const expectedImage = requiredSetting('E2E_EDITORIAL_IMAGE_URL');
  const detail = await context.request.get(`/api/updates/${updateId}/`, { headers: editorial.headers });
  expect(detail.status()).toBe(200);
  const update = await detail.json();
  expect(String(update.campaign)).toBe(campaignId);
  expect(update.image_url).toBe(expectedImage);
  const campaignResponse = await context.request.get(`/api/campaigns/${campaignId}/`);
  expect(campaignResponse.status()).toBe(200);
  const campaign = await campaignResponse.json();
  expect(campaign.status).toBe('completed');
  await page.getByRole('contentinfo').getByRole('link', { name: 'Campañas', exact: true }).click();
  await page.getByRole('button', { name: 'Completadas', exact: true }).click();
  const feed = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname.endsWith('/updates/') && url.searchParams.get('campaign') === campaignId;
  });
  await page.getByRole('link').filter({
    has: page.getByRole('heading', { name: campaign.title, exact: true }),
  }).click();
  const feedResponse = await feed;
  expect(feedResponse.status()).toBe(200);
  expect(await feedResponse.json()).toEqual(expect.arrayContaining([
    expect.objectContaining({ id: Number(updateId), image_url: expectedImage }),
  ]));
  await expect(page.getByRole('heading', { name: update.title, exact: true })).toBeVisible();
  await expectLoadedImage(page.getByAltText(update.title, { exact: true }), expectedImage);
});
