import { test, expect } from '../test-with-coverage';
import { waitForPageLoad, loginAndNavigate } from '../fixtures';
import { paceRequestsUnderRateLimit } from '../helpers/pacing';
import {
  BLOG_BROWSE,
  BLOG_DETAIL,
  BLOG_ADMIN_LIST,
  BLOG_ADMIN_CREATE,
  BLOG_ADMIN_EDIT,
  BLOG_ADMIN_CALENDAR,
  BLOG_ADMIN_DELETE,
  BLOG_ADMIN_DUPLICATE,
} from '../helpers/flow-tags';

const mockBlogPost = {
  id: 1,
  title: 'Cómo adoptar responsablemente',
  slug: 'como-adoptar-responsablemente',
  excerpt: 'Guía completa para una adopción exitosa.',
  content: '<p>Contenido del artículo sobre adopción responsable.</p>',
  category: 'adoption',
  category_display: 'Adopción',
  cover_image: '',
  author_name: 'Admin',
  published_at: '2026-03-01T12:00:00Z',
  created_at: '2026-03-01T12:00:00Z',
  status: 'published',
};

const mockBlogPost2 = {
  ...mockBlogPost,
  id: 2,
  title: 'Cuidados básicos para tu mascota',
  slug: 'cuidados-basicos-mascota',
  excerpt: 'Todo lo que necesitas saber para cuidar a tu mascota.',
};

const mockBlogListResponse = {
  results: [mockBlogPost, mockBlogPost2],
  count: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

test.describe('Blog — HTML safety', () => {
  test('preserves safe HTML without executing editorial handlers', { tag: [...BLOG_DETAIL, '@outcome:display'] }, async ({ page }) => {
    // Keep this browser probe isolated from any configured Django upstream.
    await page.route('**/api/**', (route) => route.fulfill({
      status: 200, contentType: 'application/json', body: '[]',
    }));
    const editorialPost = {
      ...mockBlogPost,
      slug: 'security-probe',
      content_json: {},
      content: '<h2>Safe editorial heading</h2><p><strong>Safe emphasis</strong></p>'
        + '<a href="/es/animals" target="_blank" rel="opener">Safe animals link</a>'
        + '<img src="/missing-security-probe" alt="Security probe" onerror="window.__blogSecurityProbe=1">'
        + '<svg onload="window.__blogSecurityProbe=1"></svg>',
    };
    await page.route('**/api/blog/**', (route) => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ ...mockBlogListResponse, results: [editorialPost], count: 1, total_pages: 1 }),
    }));
    await page.route('**/api/blog/security-probe/**', (route) => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(editorialPost),
    }));
    await page.goto('/es/blog');
    await page.getByRole('link', { name: /Cómo adoptar responsablemente/ }).click();
    await page.waitForURL(/\/es\/blog\/security-probe$/);

    await expect(page.getByRole('heading', { name: 'Safe editorial heading' })).toBeVisible();
    await expect(page.getByText('Safe emphasis')).toBeVisible();
    const link = page.getByRole('link', { name: 'Safe animals link' });
    await expect(link).toHaveAttribute('href', '/es/animals');
    await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    const image = page.getByAltText('Security probe');
    await expect(image).not.toHaveAttribute('onerror');
    // Trigger the exact browser event used by the exploit without touching real data.
    await image.dispatchEvent('error');
    expect(await page.evaluate(() => Reflect.get(window, '__blogSecurityProbe'))).toBeUndefined();
  });
});

test.describe('Blog — Public', () => {
  test.beforeEach(async ({ page }) => {
    // Mock blog detail API (must be registered before the list catch-all)
    await page.route('**/api/blog/como-adoptar-responsablemente/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockBlogPost) }),
    );
    // Mock blog list API — catch-all for any query param combination
    await page.route('**/api/blog/**', (route) => {
      // Don't intercept detail page requests (already handled above)
      if (route.request().url().includes('/api/blog/como-adoptar')) return route.fallback();
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockBlogListResponse) });
    });
  });

  test('should display blog listing page with heading and filters', { tag: [...BLOG_BROWSE, '@outcome:display'] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);

    await page.locator('header').getByRole('link', { name: 'Blog' }).click();
    await page.waitForURL(/\/blog$/, { timeout: 15_000 });
    await waitForPageLoad(page);

    await expect(page.getByRole('heading', { name: /Blog Mi Huella/i })).toBeVisible();
    await expect(page.getByPlaceholder(/Buscar artículos/i)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Todos' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Adopción' })).toBeVisible();
  });

  test('should load blog posts from API', { tag: [...BLOG_BROWSE] }, async ({ page }) => {
    await page.goto('/blog');
    await waitForPageLoad(page);

    // Wait for at least one post card to appear (web-first assertion waits for React to render)
    await expect(page.getByTestId('post-card').first()).toBeVisible({ timeout: 15_000 });
  });

  test('should navigate to blog post detail page', { tag: [...BLOG_DETAIL, '@outcome:display'] }, async ({ page }) => {
    await page.goto('/blog');
    await waitForPageLoad(page);

    // Wait for post cards to render
    const firstPostLink = page.getByTestId('post-card').first();
    await expect(firstPostLink).toBeVisible({ timeout: 15_000 });
    await firstPostLink.click();

    // Should be on a blog detail page
    await expect(page).toHaveURL(/\/blog\/.+/);

    // Should show back link and article heading
    const backLink = page.locator('main').getByRole('link', { name: 'Blog' }).first();
    await expect(backLink).toBeVisible();
  });

  test('shows an error message when the blog listing API fails', { tag: [...BLOG_BROWSE, '@outcome:failure'] }, async ({ page }) => {
    // quality: allow-no-interaction (public failure render on load — the error state IS
    // the behavior under test; there is no interactive surface to click before it renders)
    // blogStore.fetchPosts stores the raw Axios error message (blogStore.ts:70-88), not
    // app copy — the error container (blog/page.tsx:219-222) shows it verbatim.
    await page.route('**/api/blog/**', (route) =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'Internal Server Error' }) }),
    );

    await page.goto('/blog');
    await waitForPageLoad(page);

    await expect(page.getByText(/request failed with status code 500/i)).toBeVisible({ timeout: 15_000 });
  });

  // Fails if the detail page starts swallowing a server error behind its
  // "Artículo no encontrado" copy — a 500 and a genuinely missing slug would then
  // be indistinguishable to the reader, and to anyone reading a bug report.
  test('shows the server error, not "not found", when the blog detail API fails', { tag: [...BLOG_DETAIL, '@outcome:failure'] }, async ({ page }) => {
    // quality: allow-no-interaction (failure render on load — the error state IS the
    // behavior under test; the detail page has no interactive surface before it renders)
    // blogStore.fetchPost stores the raw Axios message (blogStore.ts:96-98) and the page
    // renders `{error || 'Artículo no encontrado.'}` (blog/[slug]/page.tsx:86-89), so the
    // two branches are distinguishable only by which string appears.
    // Paced because this describe has no pacing of its own: adding another page load to
    // Blog — Public pushed the suite over the rate limit and timed out the sibling
    // listing spec's navigation.
    await paceRequestsUnderRateLimit(page);
    await page.route('**/api/blog/**', (route) =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'Internal Server Error' }) }),
    );

    await page.goto(`/blog/${mockBlogPost.slug}`);
    await waitForPageLoad(page);

    await expect(page.getByText(/request failed with status code 500/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText('Artículo no encontrado.')).not.toBeVisible();
  });
});

test.describe('Blog — Admin', () => {
  // quality: allow-serial (admin blog tests require sequential auth context)
  test.describe.configure({ mode: 'serial' });

  const mockAdminBlogListResponse = {
    results: [{ ...mockBlogPost, id: 1, status: 'published' }],
    count: 1,
    page: 1,
    page_size: 10,
    total_pages: 1,
  };

  test.beforeEach(async ({ page }) => {
    // Mock validate_token so fetchMe succeeds with mock tokens
    await page.route('**/api/auth/validate_token/**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: { id: 1, email: 'admin@mihuella.com', first_name: 'Admin', last_name: 'Test', role: 'admin', is_staff: true, is_active: true } }),
      }),
    );
    // Mock admin blog API endpoints (catch-all)
    await page.route(/\/api\/blog\/admin\//, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockAdminBlogListResponse) }),
    );
  });

  test('should display admin blog list for staff users', { tag: [...BLOG_ADMIN_LIST, '@outcome:display'] }, async ({ page }) => {
    // quality: allow-no-interaction (read-only index render: the two actions this page exposes are asserted as links here and exercised by their own specs — 'creates a new blog post…' below and the calendar spec — while loginAndNavigate seeds the session by cookie rather than filling a login form)
    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    await expect(page.getByRole('heading', { name: /Blog Posts/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Nuevo Post/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Calendario/i })).toBeVisible();
  });

  test('should display admin blog create page', { tag: [...BLOG_ADMIN_CREATE, '@outcome:display'] }, async ({ page }) => {
    // quality: allow-no-interaction (render check of the EMPTY create form before any input, which is the point: filling and submitting it is covered by 'creates a new blog post and redirects to its edit page' below; loginAndNavigate seeds the session by cookie, not by filling a login form)
    await loginAndNavigate(page, 'admin', '/admin/blog/crear');
    await waitForPageLoad(page);

    await expect(page.getByRole('heading', { name: /Nuevo Blog Post/i })).toBeVisible();
    // Manual tab should be active by default
    await expect(page.getByRole('button', { name: 'Manual' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Importar JSON/i })).toBeVisible();
  });

  test('creates a new blog post and redirects to its edit page', { tag: [...BLOG_ADMIN_CREATE, '@outcome:success'] }, async ({ page }) => {
    // Registered after the describe-level beforeEach's admin-blog catch-all so it wins for create.
    await page.route('**/api/blog/admin/create/**', (route) =>
      route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id: 77, title: 'Nuevo post E2E', slug: 'nuevo-post-e2e' }) }),
    );

    await loginAndNavigate(page, 'admin', '/admin/blog/crear');
    await waitForPageLoad(page);

    // exact: true on the title fields — getByLabel matches a case-insensitive SUBSTRING, and the
    // SEO fieldset of both admin blog forms carries 'Meta título (ES)' / 'Meta title (EN)'
    // (crear/page.tsx:191-192, [id]/editar/page.tsx:222-223). Without exact the label resolves to
    // two inputs and fill() aborts on a strict-mode violation; with it, the post title is targeted
    // and a regression that renamed the SEO label could no longer silently satisfy this test.
    await page.getByLabel('Título (ES)', { exact: true }).fill('Nuevo post E2E');
    await page.getByLabel('Title (EN)', { exact: true }).fill('New E2E Post');
    await page.getByLabel('Resumen (ES)').fill('Resumen del post de prueba.');
    await page.getByLabel('Excerpt (EN)').fill('Summary of the test post.');
    await page.getByRole('button', { name: 'Crear Post' }).click();

    // handleManualSubmit redirects to the edit page for the created post, not the list
    // (admin/blog/crear/page.tsx:90) — a stale assumption here would silently pass on a
    // create that never actually reached the API.
    await expect(page).toHaveURL(/\/admin\/blog\/77\/editar/, { timeout: 10_000 });
  });

  test('shows the API validation error when creating a post is rejected', { tag: [...BLOG_ADMIN_CREATE, '@outcome:error'] }, async ({ page }) => {
    // blogStore.createPost has no try/catch, so any non-2xx response propagates as the raw
    // AxiosError (admin/blog/crear/page.tsx:89-92 only reads `err.message`, never the response
    // body) — the field-shaped body here documents intent but the surfaced text is Axios's own.
    await page.route('**/api/blog/admin/create/**', (route) =>
      route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ title_es: ['Este campo es requerido.'] }) }),
    );

    await loginAndNavigate(page, 'admin', '/admin/blog/crear');
    await waitForPageLoad(page);

    await page.getByLabel('Título (ES)', { exact: true }).fill('Título incompleto');
    await page.getByLabel('Title (EN)', { exact: true }).fill('Incomplete title');
    await page.getByLabel('Resumen (ES)').fill('Resumen');
    await page.getByLabel('Excerpt (EN)').fill('Summary');
    await page.getByRole('button', { name: 'Crear Post' }).click();

    await expect(page.getByText('Request failed with status code 400')).toBeVisible({ timeout: 10_000 });
  });

  test('shows an error message when creating a post fails at the server', { tag: [...BLOG_ADMIN_CREATE, '@outcome:failure'] }, async ({ page }) => {
    await page.route('**/api/blog/admin/create/**', (route) =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'Internal Server Error' }) }),
    );

    await loginAndNavigate(page, 'admin', '/admin/blog/crear');
    await waitForPageLoad(page);

    await page.getByLabel('Título (ES)', { exact: true }).fill('Título con fallo de servidor');
    await page.getByLabel('Title (EN)', { exact: true }).fill('Server failure title');
    await page.getByLabel('Resumen (ES)').fill('Resumen');
    await page.getByLabel('Excerpt (EN)').fill('Summary');
    await page.getByRole('button', { name: 'Crear Post' }).click();

    await expect(page.getByText('Request failed with status code 500')).toBeVisible({ timeout: 10_000 });
  });

  test('should display admin blog edit page', { tag: [...BLOG_ADMIN_EDIT, '@outcome:display'] }, async ({ page }) => {
    // Mock the individual blog post endpoint for the edit page
    await page.route('**/api/blog/admin/1/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockBlogPost, id: 1, status: 'published' }) }),
    );

    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    // Wait for the "Editar" link to appear (list has loaded)
    const editLink = page.getByRole('link', { name: /Editar/i }).first();
    await expect(editLink).toBeVisible({ timeout: 15_000 });
    await editLink.click();

    // Should be on edit page
    await expect(page).toHaveURL(/\/admin\/blog\/\d+\/editar/);
    await expect(page.getByRole('heading', { name: /Editar Post/i })).toBeVisible();
  });

  test('saves changes to an existing blog post', { tag: [...BLOG_ADMIN_EDIT, '@outcome:success'] }, async ({ page }) => {
    // Blanket handler answers GET (initial load + post-save re-fetch) and PATCH (save)
    // alike — sufficient here since the assertion only needs the save to return 2xx.
    await page.route('**/api/blog/admin/1/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockBlogPost, id: 1, status: 'published' }) }),
    );

    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    const editLink = page.getByRole('link', { name: /Editar/i }).first();
    await expect(editLink).toBeVisible({ timeout: 15_000 });
    await editLink.click();

    await expect(page).toHaveURL(/\/admin\/blog\/\d+\/editar/);

    await page.getByLabel('Título (ES)', { exact: true }).fill('Cómo adoptar responsablemente (actualizado)');
    await page.getByRole('button', { name: 'Guardar cambios' }).click();

    await expect(page.getByText('Post guardado correctamente.')).toBeVisible({ timeout: 10_000 });
  });

  test('shows an error message when saving blog post changes fails', { tag: [...BLOG_ADMIN_EDIT, '@outcome:error'] }, async ({ page }) => {
    // blogStore.updatePost has no try/catch either — same raw-Axios-message behavior as
    // blog-admin-create (page.tsx:92-93 only reads `err.message`).
    await page.route('**/api/blog/admin/1/**', (route) => {
      if (route.request().method() === 'PATCH') {
        return route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ title_es: ['Este campo es requerido.'] }) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockBlogPost, id: 1, status: 'published' }) });
    });

    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    const editLink = page.getByRole('link', { name: /Editar/i }).first();
    await expect(editLink).toBeVisible({ timeout: 15_000 });
    await editLink.click();

    await expect(page).toHaveURL(/\/admin\/blog\/\d+\/editar/);

    await page.getByLabel('Título (ES)', { exact: true }).fill('Intento de guardado fallido');
    await page.getByRole('button', { name: 'Guardar cambios' }).click();

    await expect(page.getByText('Request failed with status code 400')).toBeVisible({ timeout: 10_000 });
  });

  // Deliberately NOT a 500 twin of the spec above: the page surfaces `err.message` for
  // both statuses, so asserting the text again would be duplicate coverage wearing a
  // different tag. What is unique to the server-failure path is whether the edit
  // survives — fails if a rejected save clears the editor and the admin has to retype
  // the post they just wrote.
  test('keeps the unsaved edit in the editor when the save fails server-side', { tag: [...BLOG_ADMIN_EDIT, '@outcome:failure'] }, async ({ page }) => {
    await page.route('**/api/blog/admin/1/**', (route) => {
      if (route.request().method() === 'PATCH') {
        return route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({}) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockBlogPost, id: 1, status: 'published' }) });
    });

    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    const editLink = page.getByRole('link', { name: /Editar/i }).first();
    await expect(editLink).toBeVisible({ timeout: 15_000 });
    await editLink.click();

    await expect(page).toHaveURL(/\/admin\/blog\/\d+\/editar/);

    const titleField = page.getByLabel('Título (ES)', { exact: true });
    await titleField.fill('Borrador que no debe perderse');
    await page.getByRole('button', { name: 'Guardar cambios' }).click();

    await expect(page.getByText('Request failed with status code 500')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Post guardado correctamente.')).not.toBeVisible();
    await expect(titleField).toHaveValue('Borrador que no debe perderse');
  });

  // Pages forward to December and one click past it, so the year-rollover branch runs on
  // whatever date the suite happens to execute. Catches nextMonth() losing its year bump
  // (calendario/page.tsx:77-80): drop `setYear(y => y + 1)` and every December user paging
  // forward silently refetches the SAME year's January — a one-year-off query that the
  // month heading alone would still render plausibly.
  test('should display admin blog calendar page', { tag: [...BLOG_ADMIN_CALENDAR, '@outcome:success'] }, async ({ page }) => {
    test.slow(); // paced requests trade wall time for a deterministic transition
    // Registered before this test's own mocks (Playwright matches route handlers in reverse
    // registration order). It shadows the describe's blog-admin catch-all, which the calendar
    // mock below replaces anyway, and loginAndNavigate re-registers the auth mocks after it.
    await paceRequestsUnderRateLimit(page);

    let lastCalendarUrl = '';
    // Calendar endpoint returns an array, not paginated — override the beforeEach catch-all
    await page.route(/\/api\/blog\/admin\/calendar/, (route) => {
      lastCalendarUrl = route.request().url();
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });

    // The locale prefix is required against a deployed target: nginx hands bare /admin/ to
    // Django (it answers 302 → /admin/login/), so the Next admin panel is only reachable at
    // /<locale>/admin/*. localePrefix is 'always' (i18n/routing.ts), so this is the canonical
    // URL locally too.
    await loginAndNavigate(page, 'admin', '/es/admin/blog/calendario');
    await waitForPageLoad(page);

    // Derived from the same clock the page mounts with (page :54-58); a hardcoded month would
    // rot on the first of every month.
    const now = new Date();
    const clicksToJanuary = 11 - now.getMonth() + 1;

    await expect(page.getByRole('heading', { name: 'Calendario del Blog' })).toBeVisible({ timeout: 15_000 });
    const nextButton = page.getByRole('button', { name: /Siguiente/i });
    for (let i = 0; i < clicksToJanuary; i += 1) await nextButton.click();

    await expect(page.getByRole('heading', { name: `enero de ${now.getFullYear() + 1}` })).toBeVisible({ timeout: 10_000 });
    await expect.poll(() => lastCalendarUrl, { timeout: 10_000 }).toContain(`${now.getFullYear() + 1}-01-01`);
  });

  test('should delete a blog post with confirmation dialog', { tag: [...BLOG_ADMIN_DELETE] }, async ({ page }) => {
    let deleteRequested = false;
    await page.route(/\/api\/blog\/admin\/1\/delete/, (route) => {
      deleteRequested = true;
      return route.fulfill({ status: 204, body: '' });
    });
    // After delete, the list re-fetches and returns empty
    await page.route(/\/api\/blog\/admin\//, (route) => {
      if (route.request().url().includes('/delete')) return route.fallback();
      const body = deleteRequested
        ? { results: [], count: 0, page: 1, page_size: 10, total_pages: 1 }
        : { results: [{ ...mockBlogPost, id: 1, status: 'published' }], count: 1, page: 1, page_size: 10, total_pages: 1 };
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    });

    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    // Click Eliminar button on the post
    const deleteBtn = page.getByRole('button', { name: /Eliminar/i }).first();
    await expect(deleteBtn).toBeVisible({ timeout: 15_000 });
    await deleteBtn.click();

    // Confirmation dialog appears
    const dialog = page.getByRole('dialog', { name: /Eliminar post/i });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/no se puede deshacer/i)).toBeVisible();

    // Confirm deletion
    await dialog.getByRole('button', { name: /Eliminar/i }).click();

    // Post should be removed from the list
    await expect(page.getByText('No hay posts aún')).toBeVisible({ timeout: 10_000 });
  });

  test('should duplicate a blog post with confirmation dialog', { tag: [...BLOG_ADMIN_DUPLICATE] }, async ({ page }) => {
    let duplicated = false;
    const duplicatedPost = { ...mockBlogPost, id: 3, title: 'Copia de Cómo adoptar responsablemente', slug: 'copia-como-adoptar', status: 'draft', is_published: false };
    await page.route(/\/api\/blog\/admin\/1\/duplicate/, (route) => {
      duplicated = true;
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(duplicatedPost) });
    });
    // After duplicate, the list re-fetches and includes the new post
    await page.route(/\/api\/blog\/admin\//, (route) => {
      if (route.request().url().includes('/duplicate')) return route.fallback();
      const results = duplicated
        ? [{ ...mockBlogPost, id: 1, status: 'published' }, duplicatedPost]
        : [{ ...mockBlogPost, id: 1, status: 'published' }];
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results, count: results.length, page: 1, page_size: 10, total_pages: 1 }) });
    });

    await loginAndNavigate(page, 'admin', '/admin/blog');
    await waitForPageLoad(page);

    // Click Duplicar button on the post
    const duplicateBtn = page.getByRole('button', { name: /Duplicar/i }).first();
    await expect(duplicateBtn).toBeVisible({ timeout: 15_000 });
    await duplicateBtn.click();

    // Confirmation dialog appears
    const dialog = page.getByRole('dialog', { name: /Duplicar post/i });
    await expect(dialog).toBeVisible();

    // Confirm duplication
    await dialog.getByRole('button', { name: /Duplicar/i }).click();

    // Duplicated post should appear in the list
    await expect(page.locator('table').getByText('Copia de Cómo adoptar responsablemente')).toBeVisible({ timeout: 10_000 });
  });
});
