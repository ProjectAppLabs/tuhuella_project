import { test, expect } from '../test-with-coverage';
import { waitForPageLoad, loginAndNavigate } from '../fixtures';
import {
  HOME_LOADS,
  HOME_TO_ANIMALS,
  HOME_TO_SHELTERS,
  HOME_TO_CAMPAIGNS,
  NAVIGATION_BETWEEN_PAGES,
  NAVIGATION_HEADER,
  NAVIGATION_FOOTER,
  LOCALE_SWITCH,
  NOTIFICATION_BELL,
  NOTIFICATION_MARK_ALL_READ,
} from '../helpers/flow-tags';
import { paceRequestsUnderRateLimit } from '../helpers/pacing';

test.describe('Navigation', () => {
  test('should render home page with hero', { tag: [...HOME_LOADS] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);

    await expect(page).toHaveURL(/\/(es\/?)?$/);
    await expect(page.getByRole('heading', { name: /Cada huella cuenta/i })).toBeVisible();
  });

  test('should navigate from home to animales', { tag: [...HOME_TO_ANIMALS] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);

    await page.getByRole('link', { name: 'Ver Animales' }).click();
    await page.waitForURL(/.*animals/, { timeout: 10_000 });

    await expect(page).toHaveURL(/.*animals/);
    await expect(page.getByRole('heading', { name: /Animales en adopción/i })).toBeVisible();
  });

  test('should navigate from home to refugios', { tag: [...HOME_TO_SHELTERS] }, async ({ page }) => {
    // Mock shelters API to ensure the shelters section renders on home page
    const mockShelter = {
      id: 1, name: 'Patitas Felices', city: 'Bogotá', description: 'Refugio de animales',
      logo_url: '', cover_image_url: '', animal_count: 10, is_verified: true,
    };
    await page.route('**/api/shelters/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([mockShelter]) }),
    );

    await page.goto('/');
    await waitForPageLoad(page);

    // The shelters section heading is "Refugios destacados"; the "Ver todos" link next to it goes to /refugios
    const shelterSection = page.locator('section', { has: page.getByText('Refugios destacados') });
    await expect(shelterSection).toBeVisible({ timeout: 15_000 });
    await shelterSection.getByRole('link', { name: /Ver todos/i }).click();
    await page.waitForURL(/.*shelters/, { timeout: 10_000 });

    await expect(page).toHaveURL(/.*shelters/);
  });

  test('should navigate from home to campanas', { tag: [...HOME_TO_CAMPAIGNS] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);

    await page.getByRole('link', { name: 'Donar' }).click();
    await page.waitForURL(/.*campaigns/, { timeout: 10_000 });

    await expect(page).toHaveURL(/.*campaigns/);
  });

  test('should have working header navigation', { tag: [...NAVIGATION_HEADER] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);

    const header = page.getByRole('banner');
    await expect(header).toBeVisible();

    const links = header.locator('a');
    const linkCount = await links.count();
    expect(linkCount).toBeGreaterThan(0);
  });

  test('should have working footer', { tag: [...NAVIGATION_FOOTER] }, async ({ page }) => {
    // quality: allow-no-interaction (unauthenticated structural check of the site-wide
    // footer: the footer is a static link block with nothing to act on, so the only
    // observable behaviour is that it renders its links at all. There is no
    // loginAndNavigate here — this test never authenticates.)
    await page.goto('/');
    await waitForPageLoad(page);

    const footer = page.locator('footer');
    await expect(footer).toBeVisible();

    // Mirrors the header link-count assertion above — catches a regression where
    // the footer renders as an empty shell with no explore/account/info links.
    const footerLinks = footer.locator('a');
    const footerLinkCount = await footerLinks.count();
    expect(footerLinkCount).toBeGreaterThan(0);
  });

  test('should maintain navigation across Tu Huella pages', { tag: [...NAVIGATION_BETWEEN_PAGES, '@outcome:success'] }, async ({ page }) => {
    test.slow(); // three real hops with full prefetch; pacing trades wall time for determinism
    await paceRequestsUnderRateLimit(page);

    await page.goto('/');
    const header = page.locator('header');

    // Every header href is relative and next-intl rewrites it per route
    // (Header.tsx:203-215), so the locale prefix can break only once you are ALREADY
    // on an inner page — the regression shape is /es/animals/shelters. Chaining the
    // hops through the header is what exposes it; the six page.goto() calls this
    // replaces re-entered from scratch each time and asserted the path they had just
    // been handed, so they could not fail and exercised no header code at all.
    await header.getByRole('link', { name: 'Animales' }).click({ timeout: 10_000 });
    await page.waitForURL(/\/es\/animals$/, { timeout: 20_000 });
    await expect(page).toHaveURL(/\/es\/animals$/);
    await expect(page.locator('h1')).toHaveText('Animales en adopción');

    await header.getByRole('link', { name: 'Refugios' }).click({ timeout: 10_000 });
    await page.waitForURL(/\/es\/shelters$/, { timeout: 20_000 });
    await expect(page).toHaveURL(/\/es\/shelters$/);
    await expect(page.locator('h1')).toHaveText('Refugios verificados');

    await header.getByRole('link', { name: 'Campañas' }).click({ timeout: 10_000 });
    await page.waitForURL(/\/es\/campaigns$/, { timeout: 20_000 });
    await expect(page).toHaveURL(/\/es\/campaigns$/);
    await expect(page.locator('h1')).toHaveText('Campañas activas');
  });

  test('should switch locale from Spanish to English', { tag: [...LOCALE_SWITCH] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);

    // Verify the page loads in Spanish by default
    await expect(page.getByRole('heading', { name: /Cada huella cuenta/i })).toBeVisible();

    // The LocaleSwitcher is a radiogroup with ES/EN buttons
    const localeSwitcher = page.getByRole('radiogroup', { name: /Select language/i });
    await expect(localeSwitcher).toBeVisible();

    // Click the EN radio button to switch to English
    const enButton = localeSwitcher.getByRole('radio', { name: 'EN' });
    await enButton.click();

    // Wait for navigation first (routing.localePrefix is "always") — avoids flaky heading under load
    await expect(page).toHaveURL(/\/en(\/|$)/, { timeout: 25_000 });
    await expect(
      page.getByRole('heading', { level: 1, name: /Every paw print matters/i }),
    ).toBeVisible();
    await expect(localeSwitcher.getByRole('radio', { name: 'EN' })).toHaveAttribute('aria-checked', 'true');
  });
});

test.describe('Header Dropdowns (authenticated)', () => {
  test.describe.configure({ mode: 'serial' });

  test(
    'should open panel dropdown for shelter_admin and show shelter sub-sections',
    { tag: [...NAVIGATION_HEADER] },
    async ({ page }) => {
      await page.route('**/api/auth/validate_token/**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: { id: 2, email: 'shelter-e2e@example.com', first_name: 'Ana', last_name: 'López', role: 'shelter_admin', is_staff: false, is_active: true },
          }),
        }),
      );
      await page.route('**/api/notifications/**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], unread_count: 0 }) }),
      );
      await page.route('**/api/notifications/unread-count/**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) }),
      );

      await loginAndNavigate(page, 'shelter_admin', '/');
      await waitForPageLoad(page);

      const panelButton = page.getByRole('button', { name: /Panel Refugio/i });
      await expect(panelButton).toBeVisible({ timeout: 10_000 });
      await panelButton.click();

      await expect(page.getByRole('menuitem', { name: /Dashboard/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /Solicitudes/i })).toBeVisible();
    },
  );

  test(
    'should open account dropdown for adopter and show account links',
    { tag: [...NAVIGATION_HEADER] },
    async ({ page }) => {
      await page.route('**/api/auth/validate_token/**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: { id: 1, email: 'adopter-e2e@example.com', first_name: 'Carlos', last_name: 'Pérez', role: 'adopter', is_staff: false, is_active: true },
          }),
        }),
      );
      await page.route('**/api/notifications/**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], unread_count: 0 }) }),
      );
      await page.route('**/api/notifications/unread-count/**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) }),
      );

      await loginAndNavigate(page, 'adopter', '/');
      await waitForPageLoad(page);

      const accountButton = page.getByRole('button', { name: /Abrir menú de cuenta/i });
      await expect(accountButton).toBeVisible({ timeout: 10_000 });
      await accountButton.click();

      await expect(page.getByRole('menuitem', { name: /Mi Perfil/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /Favoritos/i })).toBeVisible();
    },
  );
});

test.describe('Notification Bell (authenticated)', () => {
  test.describe.configure({ mode: 'serial' });

  test('should open notification dropdown when bell is clicked', { tag: [...NOTIFICATION_BELL] }, async ({ page }) => {
    // Mock validate_token so fetchMe succeeds
    await page.route('**/api/auth/validate_token/**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: { id: 1, email: 'adopter-e2e@example.com', first_name: 'Carlos', last_name: 'Pérez', role: 'adopter', is_staff: false, is_active: true } }),
      }),
    );
    // Mock notification API so the bell renders correctly
    await page.route('**/api/notifications/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], unread_count: 0 }) }),
    );
    await page.route('**/api/notifications/unread-count/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) }),
    );

    await loginAndNavigate(page, 'adopter', '/');
    await waitForPageLoad(page);

    // Wait for the bell button to stabilize after auth state settles
    const bellButton = page.getByRole('button', { name: /Notificaciones/i });
    await expect(bellButton).toBeVisible({ timeout: 10_000 });
    await expect(bellButton).toBeEnabled();
    await bellButton.click();

    // Verify the notification dropdown opens
    const dropdown = page.getByTestId('notification-dropdown');
    await expect(dropdown).toBeVisible({ timeout: 5000 });

    // Verify dropdown has the notifications title header
    await expect(dropdown.getByText('Notificaciones', { exact: true })).toBeVisible();
  });
});

test.describe('Notification Mark All Read', () => {
  test(
    'user marks all notifications as read from the bell dropdown',
    { tag: [...NOTIFICATION_MARK_ALL_READ] },
    async ({ page }) => {
      let markAllReadCalled = false;

      const logs = {
        results: [
          { id: 1, event_key: 'adoption_submitted', channel: 'in_app', status: 'sent', metadata: {}, is_read: false, sent_at: '2026-05-01T10:00:00Z', created_at: '2026-05-01T10:00:00Z' },
          { id: 2, event_key: 'donation_paid', channel: 'in_app', status: 'sent', metadata: {}, is_read: false, sent_at: '2026-05-02T10:00:00Z', created_at: '2026-05-02T10:00:00Z' },
        ],
        unread_count: 3,
      };

      // General notifications handler (covers logs list); register first.
      await page.route('**/api/notifications/**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(logs) }),
      );
      // Unread count must be > 0 for the mark-all-read control to render; register after the general one.
      await page.route('**/api/notifications/unread-count/**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 3 }) }),
      );
      // Mark-all-read POST; register last so it wins for its path.
      await page.route('**/api/notifications/logs/mark-all-read/**', (route) => {
        markAllReadCalled = true;
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
      });

      await loginAndNavigate(page, 'adopter', '/');
      await waitForPageLoad(page);

      const bellButton = page.getByRole('button', { name: /Notificaciones/i });
      await expect(bellButton).toBeVisible({ timeout: 10_000 });
      await bellButton.click();

      const dropdown = page.getByTestId('notification-dropdown');
      await expect(dropdown).toBeVisible({ timeout: 5000 });

      const markAllButton = dropdown.getByRole('button', { name: /Marcar todo leído/i });
      await expect(markAllButton).toBeVisible({ timeout: 5000 });
      await markAllButton.click();

      await expect.poll(() => markAllReadCalled, { timeout: 5_000 }).toBe(true);
      await expect(markAllButton).toBeHidden({ timeout: 10_000 });
    },
  );
});

// R-navigation-01: at 412 px the open mobile menu lives inside the sticky header. Without its
// own scroll, an authenticated menu grows taller than the screen and a swipe moves the hidden
// page instead of the menu, so "Salir" (the only sign-out control on a phone) stays below the
// fold. Viewport kept local on purpose: the shared viewport helper is not part of this change.
const COMPACT_VIEWPORT = { width: 412, height: 915 };
const mobileMenuSessions = [
  { role: 'shelter_admin' as const, label: 'a shelter admin' },
  { role: 'adopter' as const, label: 'an adopter' },
];

test.describe('Header mobile menu @ 412 (celular)', { tag: ['@viewport:compact'] }, () => {
  test.use({ viewport: COMPACT_VIEWPORT, hasTouch: true });

  for (const { role, label } of mobileMenuSessions) {
    test(
      `scrolls inside the open mobile menu to reach Salir as ${label}`,
      { tag: [...NAVIGATION_HEADER, '@outcome:display', '@outcome:success'] },
      async ({ page, context }) => {
        await page.route('**/api/notifications/**', (route) =>
          route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], unread_count: 0 }) }),
        );
        await loginAndNavigate(page, role, '/');
        await waitForPageLoad(page);
        expect((await context.cookies()).some((cookie) => cookie.name === 'access_token')).toBe(true);

        await page.getByRole('button', { name: 'Toggle menu' }).click();
        const signOut = page.getByRole('banner').getByRole('button', { name: 'Salir', exact: true });
        await signOut.waitFor({ state: 'attached' });
        // A thumb swipe over the open panel must scroll the panel, never the page behind it.
        await page.mouse.move(COMPACT_VIEWPORT.width / 2, COMPACT_VIEWPORT.height / 2);
        await page.mouse.wheel(0, 1200);

        await expect.poll(() => page.evaluate(() => ({
          documentScrollY: Math.round(window.scrollY),
          headerFitsScreen: document.querySelector('header')!.getBoundingClientRect().bottom <= window.innerHeight,
        }))).toEqual({ documentScrollY: 0, headerFitsScreen: true });
        await expect(signOut).toBeInViewport({ ratio: 1 });

        await signOut.click();
        await expect.poll(async () => (await context.cookies()).some((cookie) => cookie.name === 'access_token')).toBe(false);
      },
    );
  }
});
