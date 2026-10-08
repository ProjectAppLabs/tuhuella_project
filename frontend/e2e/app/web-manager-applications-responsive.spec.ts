import type { Page } from '@playwright/test';
import { test, expect } from '../test-with-coverage';
import { loginAs } from '../fixtures';
import { WEB_MANAGER_APPLICATIONS } from '../helpers/flow-tags';
import { mockAdminApplications } from '../helpers/mock-data';

// Catches lost/duplicated applications, clipped long values, undersized detail
// links, and rows that stay tabular on a phone or portrait tablet. Navigation
// exercises the real header and detail link; only API boundaries are mocked.
const applications = {
  ...mockAdminApplications,
  results: [
    mockAdminApplications.results[0],
    {
      ...mockAdminApplications.results[1],
      animal_name: 'MiloConUnNombreMuyLargoSinEspaciosQueDebePermanecerCompleto',
      shelter_name: 'RefugioConUnNombreMuyLargoSinEspaciosQueDebePermanecerCompleto',
      user_email: 'solicitante.con.un.correo.muy.largo@un-dominio-de-prueba.example.com',
    },
  ],
};

const expectedValues = [
  'Luna', 'Refugio E2E', 'adopter-e2e@example.com', 'Enviada', '1/4/2026',
  applications.results[1].animal_name, applications.results[1].shelter_name,
  applications.results[1].user_email, 'En revisión', '25/3/2026',
];

// The round assigns this spec exclusively; the shared viewport helper is absent
// and global helpers belong to t0. Keep the canonical five sizes local here.
const viewports = [
  { name: 'compact', width: 412, height: 915, cards: true, display: 'grid', menu: 'Toggle menu', entryRole: 'link' as const },
  { name: 'portrait', width: 835, height: 1194, cards: true, display: 'grid', menu: 'Gestión Web', entryRole: 'menuitem' as const },
  { name: 'landscape', width: 1195, height: 835, cards: false, display: 'table-row', menu: 'Gestión Web', entryRole: 'menuitem' as const },
  { name: 'desktop', width: 1440, height: 900, cards: false, display: 'table-row', menu: 'Gestión Web', entryRole: 'menuitem' as const },
  { name: 'wide', width: 2560, height: 1440, cards: false, display: 'table-row', menu: 'Gestión Web', entryRole: 'menuitem' as const },
];

const json = (body: unknown) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

async function mockApplicationApis(page: Page) {
  await page.route('**/api/**', (route) => route.fulfill(json({
    count: 0, page: 1, total_pages: 1, results: [], unread_count: 0,
  })));
  await page.route('**/api/campaigns/**', (route) => route.fulfill(json([])));
  await page.route('**/api/shelters/**', (route) => route.fulfill(json([])));
  await page.route('**/api/admin/applications/**', (route) => route.fulfill(json(applications)));
  await page.route('**/api/adoptions/1/**', (route) => route.fulfill(json({
    ...applications.results[0], user: 2, form_answers: {}, notes: '', events: [],
  })));
}

for (const viewport of viewports) {
  test.describe(`Web manager applications — ${viewport.name} ${viewport.width}x${viewport.height}`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height }, hasTouch: viewport.cards, timezoneId: 'UTC' });

    test('opens an application from the complete responsive board', {
      tag: [...WEB_MANAGER_APPLICATIONS, '@outcome:success'],
    }, async ({ page }) => {
      // quality: allow-duplicate (same application navigation contract at each canonical viewport)
      await mockApplicationApis(page);
      await loginAs(page, 'web_manager');
      await page.getByRole('button', { name: viewport.menu, exact: true }).click();
      await Promise.all([
        page.waitForResponse((response) => new URL(response.url()).pathname === '/api/admin/applications/' && response.status() === 200),
        page.getByRole(viewport.entryRole, { name: 'Solicitudes', exact: true }).click(),
      ]);
      const table = page.getByRole('table', { name: 'Solicitudes de adopción' });
      const rows = table.getByRole('row').filter({ has: page.getByRole('link') });
      await expect(rows).toHaveCount(applications.count);
      // Card labels are decorative; read the same five cell values at every width.
      const fields = await table.getByRole('cell').evaluateAll((cells) => ({
        values: cells.map((cell) => Array.from(cell.childNodes)
          .filter((node) => !(node instanceof HTMLElement && node.getAttribute('aria-hidden') === 'true'))
          .map((node) => node.textContent).join('').trim()),
        unclipped: cells.every((cell) => cell.scrollWidth <= cell.clientWidth),
      }));
      expect(fields).toEqual({ values: expectedValues, unclipped: true });
      expect(await rows.evaluateAll((elements) => elements.map((row) => getComputedStyle(row).display)))
        .toEqual(applications.results.map(() => viewport.display));
      // PageTransition briefly scales its children to 0.99; measure the settled
      // targets with retrying assertions rather than a fixed animation delay.
      await expect.poll(() => table.getByRole('link').evaluateAll((links) => links.map((link) => {
        const bounds = link.getBoundingClientRect();
        return { wide: bounds.width >= 44, tall: bounds.height >= 44, fits: bounds.left >= 0 && bounds.right <= innerWidth };
      }))).toEqual(applications.results.map(() => ({ wide: true, tall: true, fits: true })));
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await table.getByRole('link', { name: 'Luna', exact: true }).click();
      await expect(page).toHaveURL(/\/es\/web-manager\/applications\/1$/);
      await expect(page.getByRole('heading', { level: 1 })).toHaveText('Luna');
    });
  });
}
