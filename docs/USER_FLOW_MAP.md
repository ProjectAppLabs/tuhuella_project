# User Flow Map

**Single source of truth for all user flows in Mi Huella.**

Use this document to understand each flow's steps, branching conditions, role restrictions, and API contracts before writing or reviewing E2E tests.

> **Flow IDs in this document match `e2e/flow-definitions.json` and `e2e/helpers/flow-tags.ts` exactly.**

**Version:** 5.11.0
**Last Updated:** 2026-09-19

---

## Table of Contents

1. [Module Index](#module-index)
2. [Home Module](#home-module)
3. [Auth Module](#auth-module)
4. [Animal Module](#animal-module)
5. [Shelter Module (Public)](#shelter-module-public)
6. [Campaign Module](#campaign-module)
7. [Adoption Module](#adoption-module)
8. [Donation Module](#donation-module)
9. [Sponsorship Module](#sponsorship-module)
10. [Favorite Module](#favorite-module)
11. [Adopter Intent Module](#adopter-intent-module)
12. [Adopter Module](#adopter-module)
13. [Shelter Panel Module](#shelter-panel-module)
14. [Admin Module](#admin-module)
15. [Navigation Module](#navigation-module)
16. [Public Module](#public-module)
17. [Blog Module](#blog-module)
18. [Blog Admin Module](#blog-admin-module)
19. [Volunteer Module](#volunteer-module)
20. [Veterinarian Module](#veterinarian-module)
21. [Web Manager Module](#web-manager-module)
22. [Manual Module](#manual-module) _(updated Phase 19: all authenticated roles; role-based filtering)_
23. [Shelter Application Module](#shelter-application-module) _(Phase 22: adopter formal shelter onboarding)_
24. [Cross-Reference](#cross-reference)

---

## Module Index

**Locale:** Rutas de la app viven bajo `[locale]` (`/es/...`, `/en/...`). Los segmentos de la columna **Frontend Route** coinciden con [`frontend/app/[locale]/`](../frontend/app/[locale]/) (sin prefijo de idioma).

| Flow ID | Name | Module | Priority | Roles | Frontend Route |
|---------|------|--------|----------|-------|----------------|
| `manual-ecosystem-browse` | Explore the complete ecosystem | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-navigate` | Navigate ecosystem levels | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-search` | Search ecosystem modules | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-search-empty` | Unmatched ecosystem search | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-tour` | Follow an ecosystem tour | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-relations` | Toggle ecosystem connections | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-share` | Restore an ecosystem selection | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-share-invalid` | Recover an invalid ecosystem link | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-access` | Explore restricted module descriptions | manual | P2 | adopter | `/manual/ecosystem` |
| `manual-ecosystem-guide` | Return to the role-filtered manual | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-auth` | Protect ecosystem access | manual | P1 | guest | `/manual/ecosystem` |
| `manual-ecosystem-orbit` | Control the ecosystem orbit | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-responsive` | Explore ecosystem cards | manual | P2 | all authenticated | `/manual/ecosystem` |
| `manual-ecosystem-locale` | Explore the English ecosystem | manual | P2 | all authenticated | `/manual/ecosystem` |
| `home-loads` | Home page loads | home | P1 | shared | `/` |
| `home-to-animals` | Navigate from home to animals | home | P2 | shared | `/` → `/animals` |
| `home-to-shelters` | Navigate from home to shelters | home | P2 | shared | `/` → `/shelters` |
| `home-to-campaigns` | Navigate from home to campaigns | home | P3 | shared | `/` → `/campaigns` |
| `auth-admin-token-handoff` | Admin token handoff redirect | auth | P3 | admin | `/admin-login` |
| `auth-sign-in-form` | Sign-in form display and interaction | auth | P1 | guest | `/sign-in` |
| `auth-login-invalid` | Login with invalid credentials | auth | P1 | guest | `/sign-in` |
| `auth-sign-up-form` | Sign-up form display and validation | auth | P1 | guest | `/sign-up` |
| `auth-forgot-password-form` | Forgot password form display | auth | P2 | guest | `/forgot-password` |
| `auth-forgot-password-reset` | Forgot password complete reset wizard | auth | P2 | guest | `/forgot-password` |
| `auth-login-redirect` | Sign-in with post-login redirect | auth | P2 | guest | `/sign-in?redirect=<path>` |
| `auth-sign-up-success` | Sign-up successful submission | auth | P2 | guest | `/sign-up` |
| `auth-protected-redirect` | Protected route redirect | auth | P1 | shared | any protected route |
| `auth-role-redirect` | Role-based navigation | auth | P2 | adopter, shelter_admin, admin | any page |
| `auth-sign-out` | Sign out | auth | P2 | adopter, shelter_admin, admin | any page |
| `auth-session-persistence` | Session persistence and token refresh | auth | P2 | adopter, shelter_admin, admin | any protected route |
| `auth-google-login` | Google OAuth login | auth | P2 | guest | `/sign-in`, `/sign-up` |
| `animal-browse` | Browse animals listing | animal | P1 | shared | `/animals` |
| `animal-filter` | Filter animals by species/size/age | animal | P2 | shared | `/animals` |
| `animal-detail` | View animal detail | animal | P1 | shared | `/animals/[animalId]` |
| `animal-gallery` | Animal gallery interaction | animal | P3 | shared | `/animals/[animalId]` |
| `shelter-browse` | Browse shelters listing | shelter | P2 | shared | `/shelters` |
| `shelter-detail` | View shelter profile | shelter | P2 | shared | `/shelters/[shelterId]` |
| `shelter-onboarding` | Legacy onboarding redirect | shelter | P4 | shared | `/shelter/onboarding` → `/shelter-application` |
| `campaign-browse` | Browse campaigns | campaign | P2 | shared | `/campaigns` |
| `campaign-detail` | View campaign detail | campaign | P2 | shared | `/campaigns/[campaignId]` |
| `adoption-submit` | Submit adoption application | adoption | P1 | adopter | `/animals/[animalId]` |
| `adoption-track` | Track adoption applications | adoption | P2 | adopter | `/my-applications` |
| `adoption-manage` | Manage adoption applications (shelter) | adoption | P1 | shelter_admin | `/shelter/applications` |
| `donation-checkout` | Donation checkout flow | donation | P1 | adopter | `/checkout/donation` |
| `donation-history` | View donation history | donation | P2 | adopter | `/my-donations` |
| `payment-confirmation` | Payment confirmation page | donation | P2 | adopter | `/checkout/confirmation` |
| `platform-support-info` | Platform support landing page | donation | P2 | shared | `/apoya-la-plataforma` |
| `donation-platform-checkout` | Platform donation checkout | donation | P1 | adopter | `/checkout/platform` |
| `sponsorship-checkout` | Sponsorship checkout flow | sponsorship | P1 | adopter | `/checkout/sponsorship` |
| `sponsorship-history` | View sponsorships | sponsorship | P2 | adopter | `/my-sponsorships` |
| `favorite-toggle` | Toggle animal favorite | favorite | P2 | adopter | `/animals/[animalId]` |
| `favorite-list` | View favorites list | favorite | P2 | adopter | `/favorites` |
| `adopter-intent-create` | Create adopter intent | adopter-intent | P3 | adopter | `/my-intent` |
| `adopter-intent-browse` | Browse adopter intents | adopter-intent | P3 | shared | `/looking-to-adopt` |
| `adopter-profile` | Adopter profile view | adopter | P2 | adopter | `/my-profile` |
| `profile-activity-feed` | View recent activity timeline on profile | adopter | P3 | adopter, shelter_admin, web_manager, admin, veterinarian | `/my-profile` |
| `shelter-admin-profile` | Shelter admin profile view | shelter-panel | P2 | shelter_admin | `/my-profile` |
| `admin-profile` | Admin profile view | admin | P2 | admin | `/my-profile` |
| `shelter-panel-dashboard` | Shelter dashboard | shelter-panel | P1 | shelter_admin | `/shelter/dashboard` |
| `shelter-panel-animals` | Shelter manage animals | shelter-panel | P1 | shelter_admin | `/shelter/animals` |
| `shelter-panel-campaigns` | Shelter manage campaigns | shelter-panel | P2 | shelter_admin | `/shelter/campaigns` |
| `shelter-panel-donations` | Shelter view donations | shelter-panel | P2 | shelter_admin | `/shelter/donations` |
| `shelter-panel-settings` | Shelter settings | shelter-panel | P2 | shelter_admin | `/shelter/settings` |
| `admin-dashboard` | Admin dashboard metrics | admin | P1 | admin | `/admin/dashboard` |
| `admin-approve-shelters` | Admin approve/reject shelters | admin | P1 | admin | `/admin/shelters/approve` |
| `admin-moderation` | Admin moderation view | admin | P2 | admin | `/admin/moderation` |
| `admin-metrics` | Admin detailed metrics | admin | P2 | admin | `/admin/metrics` |
| `admin-payments` | Admin payment audit | admin | P2 | admin | `/admin/payments` |
| `navigation-header` | Header navigation | navigation | P2 | shared | all pages |
| `navigation-footer` | Footer navigation | navigation | P4 | shared | all pages |
| `navigation-between-pages` | Cross-page navigation | navigation | P2 | shared | all pages |
| `public-faq` | FAQ page | public | P4 | shared | `/faq` |
| `public-contact` | Contact page | public | P4 | shared | `/contactanos` |
| `shelter-panel-applications` | Shelter manage adoption applications | shelter-panel | P1 | shelter_admin | `/shelter/applications` |
| `adoption-form-wizard` | Adoption form wizard completion | adoption | P1 | adopter | `/adopt/[animalId]` |
| `donation-checkout-submit` | Donation checkout form submission | donation | P1 | adopter | `/checkout/donation` |
| `sponsorship-checkout-submit` | Sponsorship checkout form submission | sponsorship | P1 | adopter | `/checkout/sponsorship` |
| `notification-preferences` | Notification preferences management | adopter | P2 | adopter | `/my-profile/notifications` |
| `notification-bell` | Notification bell interaction | navigation | P2 | adopter, shelter_admin, web_manager, admin, veterinarian | all pages |
| `notification-mark-all-read` | Mark all notifications as read | navigation | P3 | adopter, shelter_admin, web_manager, admin, veterinarian | all pages |
| `shelter-panel-updates` | Shelter manage update posts | shelter-panel | P2 | shelter_admin | `/shelter/updates` |
| `shelter-panel-update-create` | Shelter create update post | shelter-panel | P2 | shelter_admin | `/shelter/updates/create` |
| `shelter-detail-view-animals` | Shelter detail view animals link | shelter | P2 | shared | `/shelters/[shelterId]` |
| `locale-switch` | Locale switcher toggle | navigation | P2 | shared | all pages |
| `campaign-tab-toggle` | Campaign tab toggle | campaign | P3 | shared | `/campaigns` |
| `campaign-donate-cta` | Campaign donate CTA | campaign | P2 | shared | `/campaigns/[campaignId]` |
| `campaign-updates-feed` | Read updates feed on a completed campaign | campaign | P3 | shared | `/campaigns/[campaignId]` |
| `shelter-detail-gallery` | Shelter detail gallery lightbox | shelter | P3 | shared | `/shelters/[shelterId]` |
| `shelter-detail-video` | Shelter detail video modal | shelter | P3 | shared | `/shelters/[shelterId]` |
| `home-featured-animals-carousel` | Home featured animals carousel | home | P3 | shared | `/` |
| `home-active-campaigns-carousel` | Home active campaigns carousel | home | P3 | shared | `/` |
| `public-about` | About page | public | P4 | shared | `/about` |
| `public-terms` | Terms page | public | P4 | shared | `/terms` |
| `public-work-with-us` | Work with us page | public | P4 | shared | `/work-with-us` |
| `public-strategic-allies` | Strategic allies page | public | P4 | shared | `/strategic-allies` |
| `my-applications-list` | View my adoption applications | adoption | P2 | adopter | `/my-applications` |
| `blog-browse` | Blog listing page | blog | P2 | shared | `/blog` |
| `blog-detail` | Blog post detail | blog | P2 | shared | `/blog/[slug]` |
| `blog-admin-list` | Admin blog list | blog-admin | P2 | admin | `/admin/blog` |
| `blog-admin-create` | Admin blog create | blog-admin | P2 | admin | `/admin/blog/crear` |
| `blog-admin-edit` | Admin blog edit | blog-admin | P2 | admin | `/admin/blog/[id]/editar` |
| `blog-admin-calendar` | Admin blog calendar | blog-admin | P3 | admin | `/admin/blog/calendario` |
| `blog-admin-delete` | Admin delete blog post | blog-admin | P2 | admin | `/admin/blog` |
| `blog-admin-duplicate` | Admin duplicate blog post | blog-admin | P3 | admin | `/admin/blog` |
| `volunteer-apply` | Submit volunteer application | volunteer | P2 | shared | `/work-with-us/apply/[positionId]` |
| `profile-edit` | Edit user profile | adopter | P2 | adopter | `/my-profile/edit` |
| `favorites-compare` | Compare favorited animals | favorite | P3 | adopter | `/favorites` |
| `favorite-note-edit` | Edit favorite animal note | favorite | P3 | adopter | `/favorites` |
| `vet-follow-ups-list` | Veterinarian follow-ups list | veterinarian | P2 | veterinarian | `/veterinarian/follow-ups` |
| `vet-follow-up-detail` | Veterinarian follow-up detail + entry | veterinarian | P2 | veterinarian | `/veterinarian/follow-ups/[id]` |
| `web-manager-shelters` | Web manager shelter list | web-manager | P2 | web_manager | `/web-manager/shelters` |
| `web-manager-shelter-detail` | Web manager shelter detail | web-manager | P2 | web_manager | `/web-manager/shelters/[id]` |
| `web-manager-applications` | Web manager applications board | web-manager | P2 | web_manager | `/web-manager/applications` |
| `adoption-application-history` | Adoption application clinical history | adoption | P3 | adopter | `/my-applications/[id]/history` |
| `shelter-panel-campaign-detail` | Shelter campaign detail and edit | shelter-panel | P2 | shelter_admin | `/shelter/campaigns/[id]` |
| `shelter-panel-campaign-create` | Shelter create new campaign | shelter-panel | P2 | shelter_admin | `/shelter/campaigns/nueva` |
| `shelter-panel-campaign-messages` | Shelter reads and sends campaign approval messages | shelter-panel | P2 | shelter_admin | `/shelter/campaigns/[id]` |
| `web-manager-campaigns` | Web manager campaigns list | web-manager | P2 | web_manager, admin | `/web-manager/campaigns` |
| `web-manager-campaign-detail` | Web manager campaign approve/reject | web-manager | P2 | web_manager, admin | `/web-manager/campaigns/[id]` |
| `web-manager-campaign-create` | Web manager create campaign | web-manager | P2 | web_manager, admin | `/web-manager/campaigns/new` |
| `web-manager-campaign-messages` | Web manager reads and sends campaign approval messages | web-manager | P2 | web_manager, admin | `/web-manager/campaigns/[id]` |
| `manual-browse` | Interactive manual page load | manual | P2 | all authenticated | `/manual` |
| `manual-search` | Manual search and process navigation | manual | P2 | all authenticated | `/manual` |
| `manual-role-filter` | Manual content filtered by role | manual | P3 | adopter, shelter_admin, veterinarian | `/manual` |
| `web-manager-profile` | Web manager profile view | web-manager | P3 | web_manager | `/my-profile` |
| `veterinarian-profile` | Veterinarian profile view | veterinarian | P3 | veterinarian | `/my-profile` |
| `shelter-panel-animal-create` | Shelter create new animal | shelter-panel | P1 | shelter_admin | `/shelter/animals` |
| `shelter-panel-animal-edit` | Shelter edit existing animal | shelter-panel | P3 | shelter_admin | `/shelter/animals` |
| `shelter-panel-animal-archive` | Shelter archive animal | shelter-panel | P3 | shelter_admin | `/shelter/animals` |
| `auth-password-change` | Authenticated password change | auth | P2 | all authenticated | `/my-profile/edit` |
| `shelter-invite-send` | Shelter admin sends adopter invite | adopter-intent | P3 | shelter_admin | `/looking-to-adopt` |
| `shelter-invite-respond` | Adopter responds to shelter invite | adopter-intent | P3 | adopter | `/my-profile` |
| `shelter-application-submit` | Adopter submits shelter application wizard | shelter-application | P1 | adopter | `/shelter-application` |
| `shelter-application-status` | Adopter views application status | shelter-application | P2 | adopter | `/shelter-application` |
| `shelter-application-review` | Admin/web-manager approves or rejects application | shelter-application | P1 | web_manager, admin | (Django admin + API) |
| `adoption-detail-adopter` | Adopter views application detail with WhatsApp + event timeline | adoption | P2 | adopter | `/my-applications/[id]` |
| `adoption-whatsapp-shelter` | Adopter opens WhatsApp link to shelter on `interview` | adoption | P2 | adopter | `/my-applications/[id]` |
| `adoption-whatsapp-applicant` | Shelter or web_manager opens WhatsApp link to adopter on `interview` | adoption | P2 | shelter_admin, web_manager | `/shelter/applications`, `/web-manager/applications/[id]` |
| `adoption-event-create-shelter` | Shelter admin logs an event on an adoption application | adoption | P1 | shelter_admin | `/shelter/applications` |
| `adoption-event-create-web-manager` | Web manager logs an event on an adoption application | adoption | P1 | web_manager | `/web-manager/applications/[id]` |
| `adoption-detail-web-manager` | Web manager views application detail with follow-up badge + event timeline | adoption | P2 | web_manager | `/web-manager/applications/[id]` |
| `adoption-followup-reminder` | Cron-driven email reminder to web_managers every 5 days for `interview` applications | adoption | P3 | web_manager | (Huey periodic task → email) |

---

## Home Module

### home-loads

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shared |
| **Frontend route** | `/` |
| **API endpoints** | `GET /api/animals/`, `GET /api/shelters/`, `GET /api/campaigns/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/`.
2. Page renders hero section with heading and CTAs for exploring animals, shelters, and campaigns.
3. Featured animals section loads from `GET /api/animals/`.
4. Shelter spotlight section loads from `GET /api/shelters/`.
5. Active campaigns section loads from `GET /api/campaigns/`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| API unavailable | Sections show empty or skeleton state |

---

### home-to-animals

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/` → `/animales` |

**Steps:**

1. User is on the home page (`/`).
2. User clicks "Explorar Animales" CTA in the hero or featured animals section.
3. User is navigated to `/animales`.

---

### home-to-shelters

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/` → `/refugios` |

**Steps:**

1. User is on the home page (`/`).
2. User clicks shelter spotlight link or CTA.
3. User is navigated to `/refugios`.

---

### home-to-campaigns

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/` → `/campanas` |

**Steps:**

1. User is on the home page (`/`).
2. User clicks active campaigns section link or CTA.
3. User is navigated to `/campanas`.

---

### home-featured-animals-carousel

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/` |

**Preconditions:** None.

**Steps:**

1. User is on the home page (`/`).
2. Featured animals carousel renders with AnimalCard components.
3. User clicks next/prev arrows or swipe gestures to navigate cards.
4. User clicks an animal card and is navigated to `/animales/[id]`.

---

### home-active-campaigns-carousel

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/` |

**Preconditions:** None.

**Steps:**

1. User is on the home page (`/`).
2. Active campaigns carousel renders with CampaignCard components.
3. User clicks next/prev arrows or swipe gestures to navigate cards.
4. User clicks a campaign card and is navigated to `/campanas/[id]`.

---

## Auth Module

### auth-admin-token-handoff

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | admin |
| **Frontend route** | `/admin-login` |

**Preconditions:** Caller (e.g. Django admin redirect or a back-channel link) supplies `access`, `refresh`, and optionally `redirect` as URL query params.

**Steps:**

1. Browser navigates to `/admin-login?access=<token>&refresh=<token>&redirect=<path>`.
2. Page shows "Iniciando sesión..." loading state.
3. Frontend reads `access` and `refresh` from query params.
4. Tokens are written to cookies via `setTokens({ access, refresh })`.
5. Auth store is synced via `useAuthStore.getState().syncFromCookies()`.
6. Browser is redirected to `redirect` param value, or `/` if absent.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `access` or `refresh` missing from URL | Redirect to `/sign-in` immediately |
| `redirect` param absent | Redirect to `/` |

**Note:** Not covered by Playwright e2e (`expectedSpecs: 0` in `flow-definitions.json`) — all 4 token-handoff branches (missing token → `/sign-in`, tokens + redirect param → redirect target, tokens + no redirect param → `/`, loading state) are pinned by `app/[locale]/admin-login/__tests__/page.test.tsx` with concrete redirect-target assertions (`toHaveBeenCalledWith`).

---

### auth-sign-in-form

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | guest |
| **Frontend route** | `/sign-in` |
| **API endpoints** | `POST /api/auth/sign_in/` |

**Preconditions:** User is not authenticated. A registered account exists.

**Steps:**

1. User navigates to `/sign-in`.
2. Page renders form with **Email**, **Password** fields and **Sign in** button.
3. User fills in email and password.
4. User clicks **Sign in**.
5. Frontend sends `POST /api/auth/sign_in/` with `{ email, password }`.
6. Backend validates credentials and returns `{ access, refresh }` (HTTP 200).
7. Frontend stores tokens in cookies (`access_token`, `refresh_token`).
8. Frontend redirects to `/` or the originally requested page.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Empty email or password | HTML `required` prevents submission |
| Account inactive | `403 { error: "Account is inactive" }` — error below form |

---

### auth-login-invalid

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | guest |
| **Frontend route** | `/sign-in` |
| **API endpoints** | `POST /api/auth/sign_in/` |

**Preconditions:** User is not authenticated.

**Steps:**

1. User navigates to `/sign-in`.
2. User fills in invalid email/password combination.
3. User clicks **Sign in**.
4. Backend returns `401 { error: "Invalid credentials" }`.
5. Error message displayed below the form.
6. User stays on `/sign-in`.

---

### auth-sign-up-form

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | guest |
| **Frontend route** | `/sign-up` |
| **API endpoints** | `POST /api/auth/sign_up/` |

**Preconditions:** User is not authenticated.

**Steps:**

1. User navigates to `/sign-up`.
2. Page renders form: **First Name**, **Last Name**, **Email**, **Password**, **Confirm Password**, **Create account** button.
3. User fills in all fields.
4. User clicks **Create account**.
5. Frontend validates passwords match and length >= 8.
6. Frontend sends `POST /api/auth/sign_up/` with `{ email, password, first_name, last_name }`.
7. Backend creates user and returns `{ access, refresh }` (HTTP 201).
8. Frontend stores tokens and redirects to `/`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Passwords do not match | Client error: "Passwords do not match" — no API call |
| Password < 8 chars | Client error: "Password must be at least 8 characters" — no API call |
| Email already registered | `400 { error: "User with this email already exists" }` |
| Missing email or password | `400 { error: "Email and password are required" }` |

---

### auth-forgot-password-form

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | guest |
| **Frontend route** | `/forgot-password` |
| **API endpoints** | `POST /api/auth/send_passcode/` |

**Preconditions:** User is not authenticated.

**Steps:**

1. User navigates to `/forgot-password`.
2. Page renders email input and **Send verification code** button (step = `email`).
3. User types in the email field and can click the button.
4. Navigation from `/sign-in` → `/forgot-password` link works.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No GOOGLE_CLIENT_ID set | Google button absent, email form still renders |

---

### auth-forgot-password-reset

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | guest |
| **Frontend route** | `/forgot-password` |
| **API endpoints** | `POST /api/auth/send_passcode/`, `POST /api/auth/verify_passcode_and_reset_password/` |

**Preconditions:** User is not authenticated. A registered account exists.

**Steps:**

1. User navigates to `/forgot-password`, enters valid email, clicks **Send verification code**.
2. Frontend POSTs `{ email, locale }` to `/api/auth/send_passcode/`. Backend generates `PasswordCode` and sends localized email.
3. UI transitions to step = `code`. User sees Code + New Password + Confirm Password fields.
4. User enters the 6-digit code and a password that passes `validate_password()` (≥8 chars, not all-numeric, not common).
5. Frontend POSTs `{ email, code, new_password }` to `/api/auth/verify_passcode_and_reset_password/`.
6. Backend verifies code (not used, not expired), sets new password, marks code used. Returns HTTP 200.
7. Success message shown; user redirected to `/sign-in`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Email not registered | API returns `200` with generic message (no user enumeration) |
| Invalid / expired code | `400 { error: "Invalid or expired code" }` |
| Weak password (< 8 chars, common, all-numeric) | `400 { error: "..." }` from `validate_password()` |
| Passwords do not match | Client-side error — no API call |
| "Back to email" clicked | UI returns to step A |

---

### auth-login-redirect

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | guest |
| **Frontend route** | `/sign-in?redirect=<path>` |
| **API endpoints** | `POST /api/auth/sign_in/` |

**Preconditions:** User lands on `/sign-in` with a `?redirect=` query param (typically set by a protected-route gate).

**Steps:**

1. Browser navigates to `/sign-in?redirect=/my-applications`.
2. `safeRedirectTarget()` validates the param: accepts `/`-starting paths, rejects absolute URLs and `//host` paths.
3. User enters valid credentials and submits.
4. On success, `router.replace('/my-applications')` fires instead of `router.replace('/')`.
5. User lands on the intended page.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `redirect=https://evil.com` | Unsafe — falls back to `/` |
| `redirect=//host/path` | Unsafe (protocol-relative) — falls back to `/` |
| No `redirect` param | Falls back to `ROUTES.HOME` (`/`) |

---

### auth-sign-up-success

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | guest |
| **Frontend route** | `/sign-up` |
| **API endpoints** | `POST /api/auth/sign_up/` |

**Preconditions:** User is not authenticated. Email not yet registered.

**Steps:**

1. User navigates to `/sign-up`.
2. User fills all required fields: first name, last name, email, password, confirm password, and accepts terms.
3. Passwords match and meet strength requirements.
4. User submits form.
5. API creates account, returns tokens or redirects to sign-in.
6. User lands on `/sign-in` (or home) after successful registration.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Email already registered | `400` error — email taken message shown |
| Passwords don't match | Client-side validation — no API call |
| Terms not accepted | Form blocked — no API call |

---

### auth-protected-redirect

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shared |
| **Frontend route** | any protected route |

**Preconditions:** User is NOT authenticated (no tokens in cookies).

**Steps:**

1. Unauthenticated user navigates to a protected route (e.g., `/favoritos`, `/refugio/dashboard`).
2. `useRequireAuth()` hook detects missing tokens.
3. User is redirected to `/sign-in`.

**Outcomes:** `success`, `error`. Un refresh rechazado definitivamente con 401 elimina las credenciales y redirige a iniciar sesión.

---

### auth-role-redirect

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter, shelter_admin, admin |
| **Frontend route** | any page |

**Preconditions:** User is authenticated.

**Steps:**

1. Authenticated user loads any page.
2. Header renders role-specific navigation links:
   - **adopter**: Favoritos, Mis Solicitudes, Mis Donaciones, Mis Apadrinamientos
   - **shelter_admin**: Panel Refugio (with sub-nav to dashboard, animales, etc.)
   - **admin**: Admin panel links (Dashboard, Aprobar Refugios, etc.)

**Note:** Not covered by Playwright e2e (`expectedSpecs: 0` in `flow-definitions.json`) — role-specific nav is pinned at the unit layer (`components/layout/__tests__/Header.test.tsx` asserts the per-role dropdown contents for shelter_admin/web_manager/admin). The only e2e spec that ever existed for this flow was a mistagged copy of the unauthenticated-redirect check already covered by `auth-protected-redirect`.

---

### auth-sign-out

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter, shelter_admin, admin |
| **Frontend route** | any page |
| **API endpoints** | None (client-side only) |

**Preconditions:** User is authenticated.

**Steps:**

1. User clicks **Sign out** button in header.
2. Frontend clears JWT tokens from cookies via `authStore.signOut()`.
3. User is redirected to `/sign-in` by the auth guard.

---

### auth-session-persistence

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter, shelter_admin, admin |
| **Frontend route** | any protected route |
| **API endpoints** | `GET /api/auth/validate_token/`, `POST /api/token/refresh/` |

**Preconditions:** User has valid tokens in cookies.

**Steps:**

1. User navigates to a protected route.
2. Frontend reads `access_token` from cookies.
3. Frontend sends `GET /api/auth/validate_token/` with Bearer token.
4. Backend validates JWT and returns `{ valid: true, user: { id, email, first_name, last_name, role, is_staff } }`.
5. User is shown the protected content.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No tokens in cookies | Redirect to `/sign-in` via `useRequireAuth` hook |
| Access token expired | Frontend calls `POST /api/token/refresh/` with refresh token |
| Refresh token expired | Redirect to `/sign-in` |
| Validación o refresh temporalmente indisponible (503, red o timeout) | Conserva credenciales y sesión; una nueva carga permite reintentar |
| Refresh rechazado definitivamente con 401 | Elimina credenciales y redirige a `/sign-in` |

**Outcomes:** `success` para acceso/renovación válida; `failure` para recuperación tras un fallo transitorio.

---

### auth-google-login

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | guest |
| **Frontend route** | `/sign-in`, `/sign-up` |
| **API endpoints** | `POST /api/auth/google_login/` |

**Preconditions:** `NEXT_PUBLIC_GOOGLE_CLIENT_ID` env var is set. User is not authenticated.

**Steps:**

1. User navigates to `/sign-in` or `/sign-up`.
2. Google Sign-In button rendered via `@react-oauth/google`.
3. User clicks Google button and completes OAuth consent.
4. Frontend receives credential JWT, decodes `email`, `given_name`, `family_name`, `picture`.
5. Frontend sends `POST /api/auth/google_login/` with `{ credential, email, given_name, family_name, picture }`.
6. Backend validates token via Google tokeninfo, gets or creates user.
7. Backend returns `{ access, refresh, created, google_validated }` (HTTP 200).
8. Frontend stores tokens and redirects to `/`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` missing | "Missing NEXT_PUBLIC_GOOGLE_CLIENT_ID" shown instead of button |
| Credential missing | `400 { error: "Google credential is required" }` |
| Invalid credential (prod) | `401 { error: "Invalid Google credential" }` |
| Audience mismatch (prod) | `401 { error: "Invalid Google client" }` |
| New user | User created with unusable password; `created: true` |
| Existing user | Matched by email; names updated if blank |

**Note:** Not covered by Playwright e2e (`expectedSpecs: 0` in `flow-definitions.json`) — OAuth happens inside a real Google-hosted popup and cannot be driven headlessly without live Google credentials; the button's render/click wiring is unit territory.

---

### auth-password-change

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter, shelter_admin, admin, web_manager, veterinarian |
| **Frontend route** | Sin formulario de cambio de contraseña accesible |
| **API endpoints** | `POST /api/auth/update_password/` |

**Contrato backend:** requiere autenticación y contraseña actual. Una contraseña actual incorrecta o una contraseña nueva corta, común, numérica o similar al usuario devuelve 400 sin cambiar la contraseña original. Una contraseña nueva válida devuelve 200.

**Cobertura:** `expectedSpecs: 0` conserva la exención E2E porque no hay formulario en la UI. El comportamiento y los casos negativos se verifican con pytest en `backend/base_feature_app/tests/views/test_auth_endpoints.py`.

---

## Animal Module

### animal-browse

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shared |
| **Frontend route** | `/animales` |
| **API endpoints** | `GET /api/animals/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/animales`.
2. Page displays animal cards grid with loading skeletons.
3. Frontend fetches `GET /api/animals/` via `animalStore.fetchAnimals()`.
4. Each card shows name, species, breed, age, shelter, and thumbnail.
5. Each card links to `/animales/[id]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| API loading | Skeleton grid shown |
| No animals | Empty state message |

---

### animal-filter

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/animales` |
| **API endpoints** | `GET /api/animals/?species=...&size=...&age_range=...` |

**Preconditions:** User is on `/animales`.

**Steps:**

1. User applies filters (species, size, age_range, gender) via filter controls.
2. Frontend sends filtered `GET /api/animals/` request.
3. Grid updates with filtered results.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No results for filter | Empty state with "No animals match your filters" |
| Reset filters | Grid returns to unfiltered view |

---

### animal-detail

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shared |
| **Frontend route** | `/animales/[id]` |
| **API endpoints** | `GET /api/animals/<id>/` |

**Preconditions:** Animal with given ID exists.

**Steps:**

1. User clicks an animal card or navigates to `/animales/[id]`.
2. Page renders animal info (name, species, breed, age, size, description, health status).
3. Gallery images displayed via Swiper carousel.
4. CTAs: **Solicitar adopción**, **Apadrinar**, **Agregar a favoritos**.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Not authenticated | Adoption/sponsorship CTAs redirect to `/sign-in` |
| Animal already favorited | Heart icon shows filled state |
| Animal status `adopted` | Adoption CTA disabled |

---

### animal-gallery

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/animales/[id]` |

**Preconditions:** Animal detail page is loaded. Animal has gallery images.

**Steps:**

1. Gallery section renders with Swiper carousel.
2. User can swipe/click through images.
3. Pagination bullets indicate current position.

---

## Shelter Module (Public)

### shelter-browse

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/refugios` |
| **API endpoints** | `GET /api/shelters/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/refugios`.
2. Page displays shelter cards grid.
3. Each card shows name, city, verification badge, and description.
4. Each card links to `/refugios/[id]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| API loading | Skeleton grid shown |
| No shelters | Empty state message |

---

### shelter-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/refugios/[id]` |
| **API endpoints** | `GET /api/shelters/<id>/`, `GET /api/animals/?shelter=<id>`, `GET /api/campaigns/?shelter=<id>` |

**Preconditions:** Shelter with given ID exists.

**Steps:**

1. User clicks a shelter card or navigates to `/refugios/[id]`.
2. Page renders shelter profile: name, legal name, description, city, contact info, verification badge.
3. Shelter's animals section loads.
4. Shelter's campaigns section loads.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Shelter not verified | No verification badge shown |
| No animals | "No animals yet" empty state |
| No campaigns | "No campaigns yet" empty state |

---

### shelter-onboarding

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/shelter/onboarding` (legacy redirect → `/shelter-application`) |
| **API endpoints** | none (page is a client-side redirect) |

**Preconditions:** None.

**Steps:**

1. User (any role, even guest) lands on `/shelter/onboarding` (e.g., from a stale bookmark or external link).
2. Page mounts and immediately calls `router.replace('/shelter-application')`.
3. User ends up on `/shelter-application`, where the formal Phase 22 wizard runs (or the status view if they already have an application). Guests are funneled to `/sign-in` by `useRequireAuth` on the destination page.

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| Guest | `/shelter-application` redirects them to `/sign-in` |
| Authenticated `adopter` | Lands in the wizard or status view |
| Authenticated `shelter_admin` | Lands in `/shelter-application` and is bounced back to `/my-profile` |

**Note:** the old form that called `POST /api/shelters/create/` was removed in the cleanup after Phase 22. The endpoint itself still exists but is now restricted to `admin` and `web_manager` roles for operational use; adopters and shelter_admins receive HTTP 403 with a hint to use the formal application flow.

---

### shelter-detail-view-animals

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/refugios/[id]` |
| **API endpoints** | `GET /api/animals/?shelter=<id>` |

**Preconditions:** Shelter with given ID exists and has published animals.

**Steps:**

1. User is on shelter detail page (`/refugios/[id]`).
2. User clicks **View Animals** button.
3. User is navigated to `/animales` with shelter filter applied.
4. Animal listing shows only animals belonging to that shelter.

---

### shelter-detail-gallery

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/refugios/[id]` |

**Preconditions:** Shelter has gallery images.

**Steps:**

1. User is on shelter detail page.
2. Gallery section renders shelter images in a grid.
3. User clicks an image to open lightbox modal.
4. Lightbox displays full-size image.
5. User clicks outside image or X button to close lightbox.

---

### shelter-detail-video

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/shelters/[shelterId]` |

**Preconditions:** Shelter has a `video_url` value (set by platform staff from Django admin).

**Steps:**

1. User is on shelter detail page.
2. A "Ver video" button is rendered above the gallery section.
3. User clicks the button.
4. A modal opens with an HTML5 `<video controls>` player whose `src` matches `shelter.video_url`.
5. User closes the modal via the close button, the backdrop, or the `Escape` key — the video stops playing.

When the shelter has no `video_url`, the button is not rendered.

---

## Campaign Module

### campaign-browse

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/campanas` |
| **API endpoints** | `GET /api/campaigns/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/campanas`.
2. Page displays campaign cards with progress bars.
3. Each card shows title, shelter name, goal amount, raised amount, and progress percentage.
4. Each card links to `/campanas/[id]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| API loading | Skeleton grid shown |
| No campaigns | Empty state message |

---

### campaign-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/campanas/[id]` |
| **API endpoints** | `GET /api/campaigns/<id>/`, `GET /api/updates/?campaign=<id>` |

**Preconditions:** Campaign with given ID exists.

**Steps:**

1. User clicks a campaign card or navigates to `/campanas/[id]`.
2. Page renders campaign info: title, description, shelter name, progress bar, dates.
3. Donation CTA button visible.
4. Updates feed section loads related update posts.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Not authenticated | Donate CTA redirects to `/sign-in` |
| Campaign completed | Donate CTA disabled, "Goal reached" badge shown |

---

### campaign-tab-toggle

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/campanas` |
| **API endpoints** | `GET /api/campaigns/` |

**Preconditions:** None.

**Steps:**

1. User is on campaigns listing page (`/campanas`).
2. Page shows Active and Completed tab toggle.
3. By default, Active tab is selected showing active campaigns.
4. User clicks Completed tab.
5. Listing updates to show only completed campaigns.
6. User clicks Active tab to return to active campaigns.

---

### campaign-donate-cta

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/campanas/[id]` → `/checkout/donacion` |

**Preconditions:** Campaign exists and is active. User is authenticated.

**Steps:**

1. User is on campaign detail page (`/campanas/[id]`).
2. User clicks **Donate** CTA button.
3. User is navigated to `/checkout/donacion` with campaign context (campaign ID pre-filled).

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Not authenticated | Redirects to `/sign-in` |

---

## Adoption Module

### campaign-updates-feed

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/campaigns/[campaignId]` |
| **API endpoints** | `GET /api/campaigns/[pk]/`, `GET /api/updates/` |

**Preconditions:** A campaign with status `completed` exists.

**Steps:**

1. Visitor navigates to `/campaigns/[campaignId]` of a completed campaign.
2. Page loads the campaign via `GET /api/campaigns/[pk]/`.
3. When `campaign.status === 'completed'`, the progress-updates feed loads via `GET /api/updates/`.
4. Each update renders its title, body, and image when present.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Campaign not completed | Updates feed hidden |
| No updates for the campaign | Empty state / feed omitted |

---

### adoption-submit

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/animales/[id]` |
| **API endpoints** | `POST /api/adoptions/create/` |

**Preconditions:** User is authenticated. Animal status is `published`.

**Steps:**

1. User clicks **Solicitar adopción** on animal detail page.
2. Adoption form displays with questionnaire fields.
3. User fills form and submits.
4. Frontend sends `POST /api/adoptions/create/` with `{ animal, form_answers, notes }`.
5. Backend creates `AdoptionApplication` with status `submitted` (HTTP 201).
6. Success message shown; user can track at `/mis-solicitudes`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| User already applied for this animal | `400` error — "Application already exists" |
| Animal status not `published` | Adoption CTA disabled |

---

### adoption-track

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/mis-solicitudes` |
| **API endpoints** | `GET /api/adoptions/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/mis-solicitudes`.
2. Page loads user's adoption applications via `GET /api/adoptions/`.
3. Each application shows animal name, shelter name, status badge, and submission date.
4. Status badges: Submitted (blue), Reviewing (amber), Interview (purple), Approved (green), Rejected (red).

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No applications | Empty state: "No has enviado solicitudes aún" |
| API loading | Loading spinner |

---

### adoption-manage

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/solicitudes` |
| **API endpoints** | `GET /api/adoptions/`, `PATCH /api/adoptions/<id>/status/` |

**Preconditions:** User is authenticated as shelter_admin. Shelter owns the animals with applications.

**Steps:**

1. Shelter admin navigates to `/refugio/solicitudes`.
2. Page loads applications for shelter's animals.
3. Each application shows applicant email, animal name, status, submission date.
4. Admin clicks status action buttons: **Revisar** → **Entrevista** → **Aprobar** / **Rechazar**.
5. Frontend sends `PATCH /api/adoptions/<id>/status/` with `{ status }`.
6. Application status updates in the list.

---

### adoption-form-wizard

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/adopt/[animalId]` |
| **API endpoints** | `POST /api/adoptions/create/` |

**Preconditions:** User is authenticated with `adopter` role. Animal exists with `published` status.

**Steps:**

1. User clicks **Solicitar adopción** on animal detail page.
2. Adoption wizard opens at Step 1 (Questionnaire) with 6 sections:
   - Basic Info: full name, phone, email, city (required).
   - Home & Context: housing type, yard, hours alone.
   - Experience: previous pets, current pets, experience level.
   - Compatibility: children, children ages, cats, other dogs.
   - Commitment: vaccination, sterilization, follow-up checkboxes (required).
   - Logistics: availability date, transport, delivery preference, motivation.
3. User fills all required fields and clicks **Continue**.
4. Step 2 (Review) displays read-only summary of answers by section.
5. User reviews and clicks **Continue**.
6. Step 3 (Submit) shows optional notes textarea and **Submit** button.
7. User optionally adds notes and clicks **Submit**.
8. Frontend sends `POST /api/adoptions/create/` with `{ animal, form_answers, notes }`.
9. Backend creates `AdoptionApplication` with `status=submitted` (HTTP 201).
10. Success message displayed.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Required fields missing | Form validation prevents advancing to next step |
| Commitment checkboxes unchecked | Cannot proceed past questionnaire |
| API error | Error message shown, form remains on submit step |

---

### my-applications-list

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/mis-solicitudes` |
| **API endpoints** | `GET /api/adoptions/` |

**Preconditions:** User is authenticated with `adopter` role.

**Steps:**

1. User navigates to `/mis-solicitudes`.
2. Page loads adoption applications from `GET /api/adoptions/`.
3. Each application card shows animal name, shelter name, submission date, and status badge.
4. Status badges display: Submitted, Reviewing, Interview, Approved, Rejected.
5. Each card links to `/my-applications/[id]` for the new follow-up detail view.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No applications | Empty state message shown |

---

### adoption-detail-adopter

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/my-applications/[id]` |
| **API endpoints** | `GET /api/adoptions/<pk>/` |

**Preconditions:** Authenticated `adopter` is the applicant of the requested application.

**Steps:**

1. Adopter opens a card from `/my-applications`.
2. Page calls `GET /api/adoptions/<pk>/`; serializer returns `events`, `next_follow_up_due_at`, `shelter_whatsapp` (only when status is `interview` or `approved`), and `applicant_whatsapp` (always `null` for the adopter themself).
3. Page renders the status badge, the linear timeline, the WhatsApp card to the shelter when `shelter_whatsapp` is present, the read-only event timeline, and a link to `/my-applications/[id]/history`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Status is `submitted` / `reviewing` / `rejected` | WhatsApp card hidden |
| `events` empty | Timeline shows neutral empty-state copy |
| Application not found or unauthorized | "Not found" message |

---

### adoption-whatsapp-shelter

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/my-applications/[id]` |
| **API endpoints** | (none — opens `wa.me/<digits>` in a new tab) |

**Preconditions:** Application status is `interview` or `approved` and the shelter has a phone on file.

**Steps:**

1. Backend exposes `shelter_whatsapp = Shelter.phone` only when the gating conditions hold.
2. Frontend renders `WhatsAppContactCard` with a `wa.me/<sanitized-digits>?text=<encoded-prefilled-message>` link in a new tab.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `Shelter.phone` is empty after sanitization (no digits) | Card returns `null` |

---

### adoption-event-create-shelter

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shelter_admin |
| **Frontend route** | `/shelter/applications` (inline expansion) |
| **API endpoints** | `POST /api/adoptions/<pk>/events/`, `GET /api/adoptions/<pk>/` |

**Preconditions:** Application is in `interview` or `approved` status; the user manages the shelter that owns the animal.

**Steps:**

1. Shelter admin clicks "Detalle" on an application card; the detail is fetched and cached in `applicationsById`.
2. `AdoptionEventTimeline` shows "Registrar evento" because the role can write.
3. The modal validates the date is not in the future and the description is non-empty (≤ 2000 chars).
4. `POST /api/adoptions/<pk>/events/` creates the event; backend resets `application.next_follow_up_due_at = now() + 5d`.
5. Store applies the same optimistic update so the badge in the web_manager view does not need a refetch.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| User does not manage the shelter | 403 Permission denied |
| Description blank or only whitespace | 400 with `description` field error |
| `event_date` in the future | 400 with `event_date` field error |

---

### adoption-whatsapp-applicant

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin, web_manager |
| **Frontend route** | `/shelter/applications` |
| **API endpoints** | `GET /api/adoptions/`, `GET /api/adoptions/[pk]/` |

**Preconditions:** Shelter admin (or web manager) is authenticated; the application status is `interview` or `approved` and the applicant has a WhatsApp number on file.

**Steps:**

1. Shelter admin opens `/shelter/applications` and expands an application row ("Detalle").
2. The application detail loads via `GET /api/adoptions/[pk]/`.
3. When the status is `interview`/`approved` and `applicant_whatsapp` is set, a "Escribir al adoptante" WhatsApp card renders.
4. Clicking it opens `https://wa.me/<applicant_number>` with a prefilled message in a new tab.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No `applicant_whatsapp` | WhatsApp card not shown |
| Status not interview/approved | WhatsApp card not shown |

---

### adoption-detail-web-manager

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/applications/[id]` |
| **API endpoints** | `GET /api/adoptions/[pk]/` |

**Preconditions:** Web manager or admin is authenticated.

**Steps:**

1. Web manager navigates to `/web-manager/applications/[id]`.
2. The application loads via `GET /api/adoptions/[pk]/`.
3. The detail renders the animal name (H1), applicant email ("Solicitante"), submission date, status badge, and the process-events timeline.
4. When the status is `interview` and a follow-up is due, a follow-up reminder banner shows.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Application not found | "No encontramos la solicitud." |
| Still loading | "Cargando solicitud..." |

---

### adoption-event-create-web-manager

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/applications/[id]` |
| **API endpoints** | `POST /api/adoptions/<pk>/events/`, `GET /api/adoptions/<pk>/` |

**Preconditions:** Authenticated user has role `web_manager` or `admin`. The application is in `interview` or `approved` status (button hidden otherwise).

**Steps:**

1. Web manager opens the detail page from the table on `/web-manager/applications`.
2. Header shows the "Próximo recordatorio en N días" amber badge using `next_follow_up_due_at`.
3. Web manager registers an event; `_bump_follow_up()` reprograms the timer to +5 days.
4. The page does not refetch — the store's optimistic update reflects both the new event and the new `next_follow_up_due_at`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `next_follow_up_due_at` is in the past | Badge swaps "Programado en" for "Vencido hace" copy |
| Status leaves `interview` (e.g., approved/rejected) | `clear_follow_up()` runs server-side; badge disappears |

---

### adoption-followup-reminder

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | web_manager |
| **Frontend route** | n/a (Huey → email) |
| **API endpoints** | n/a (background task) |

**Preconditions:**
- `ADOPTION_FOLLOW_UPS_ENABLED=True` in env (default).
- `tuhuella-huey.service` runs with `--periodic`.

**Steps:**

1. Cron `crontab(hour='9', minute='0')` runs `adoption_interview_follow_ups`.
2. Service queries applications in `interview` with `next_follow_up_due_at__lte=now()` (annotated with `Max('events__event_date')`).
3. For each due application, every active `User.role=='web_manager'` receives `dispatch_notification('adoption_interview_follow_up_due', manager, ctx)`.
4. The application's `next_follow_up_due_at` is reset to `now() + 5 days` even if no event was logged, so the next reminder is exactly five days later.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Flag `ADOPTION_FOLLOW_UPS_ENABLED=False` | Task no-ops with a `logger.info` message |
| No active web managers | Task logs and returns 0 dispatches |
| Application archived (`archived_at__isnull=False`) | Excluded from the query |

---

## Donation Module

### donation-checkout

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/checkout/donacion` |
| **API endpoints** | `POST /api/payments/create-intent/` (placeholder) |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/checkout/donacion` (from campaign or shelter).
2. Page shows preset amounts, custom amount input, payment method selector.
3. Placeholder banner indicates Wompi integration is not yet active.
4. User selects amount and payment method, clicks **Donar**.
5. Simulated processing (1.5s delay).
6. Redirect to `/checkout/confirmacion?type=donation&status=placeholder`.

---

### donation-history

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/mis-donaciones` |
| **API endpoints** | `GET /api/donations/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/mis-donaciones`.
2. Page loads user's donations via `GET /api/donations/`.
3. Each donation shows amount, target (shelter or campaign), status badge, and date.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No donations | Empty state: "No has realizado donaciones aún" |
| API loading | Loading spinner |

---

### payment-confirmation

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/checkout/confirmacion` |

**Preconditions:** User was redirected from donation or sponsorship checkout.

**Steps:**

1. User lands on `/checkout/confirmacion` with query params (`type`, `status`).
2. Page shows confirmation message based on payment type and status.
3. Links to view history (`/mis-donaciones` or `/mis-apadrinamientos`) and return to home.

---

### donation-checkout-submit

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/checkout/donacion` |
| **API endpoints** | `POST /api/donations/create/`, `POST /api/payments/create-intent/` |

**Preconditions:** User is authenticated with `adopter` role.

**Steps:**

1. User navigates to `/checkout/donacion`.
2. Page renders preset donation amount buttons (e.g., 10,000 / 50,000 COP) and custom amount input.
3. User selects a preset amount or enters custom amount.
4. User selects payment method: Tarjeta (card), PSE, or Nequi.
5. User optionally enters a message in the textarea.
6. Amount summary updates dynamically.
7. User clicks **Submit** / **Donar** button.
8. Frontend sends `POST /api/donations/create/` followed by `POST /api/payments/create-intent/`.
9. Payment provider (Wompi) processes the transaction.
10. User is redirected to `/checkout/confirmacion` with status.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No amount selected | Submit button disabled |
| No payment method selected | Submit button disabled |
| Payment fails | Error message shown, user remains on checkout |

---

### platform-support-info

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/apoya-la-plataforma` |
| **API endpoints** | None |

**Preconditions:** None.

**Steps:**

1. User navigates to `/apoya-la-plataforma`.
2. Page renders hero with platform support CTA.
3. Cost breakdown cards show platform operating costs.
4. Transparency section describes how funds are used.
5. Comparison grid lists 5 ways to support Tuhuella.
6. User clicks the CTA button to proceed to the platform donation checkout.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| User not authenticated | CTA redirects to `/sign-in?redirect=/checkout/platform` |
| User authenticated | CTA navigates directly to `/checkout/platform` |

---

### donation-platform-checkout

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/checkout/platform` |
| **API endpoints** | `POST /api/donations/create/`, `POST /api/payments/create-intent/` |

**Preconditions:** User is authenticated (redirect to `/sign-in` otherwise).

**Steps:**

1. User navigates to `/checkout/platform`.
2. Page renders preset donation amounts and custom amount input (same pattern as shelter donations).
3. User selects an amount.
4. User selects payment method (card / PSE / Nequi).
5. User submits the form.
6. Frontend sends `POST /api/donations/create/` with `dest=platform` context, then `POST /api/payments/create-intent/`.
7. User is redirected to `/checkout/confirmation?dest=platform`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Unauthenticated | Redirected to `/sign-in?redirect=/checkout/platform` |
| No amount selected | Submit disabled |
| Payment fails | Error shown inline; user stays on checkout |

---

## Sponsorship Module

### sponsorship-checkout

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/checkout/apadrinamiento` |
| **API endpoints** | `POST /api/payments/create-intent/` (placeholder) |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/checkout/apadrinamiento` (from animal detail page).
2. Page shows amount input, frequency selector (monthly/one-time), payment method selector.
3. Placeholder banner indicates Wompi integration is not yet active.
4. User selects amount, frequency, and payment method, clicks **Apadrinar**.
5. Simulated processing (1.5s delay).
6. Redirect to `/checkout/confirmacion?type=sponsorship&status=placeholder`.

---

### sponsorship-history

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/mis-apadrinamientos` |
| **API endpoints** | `GET /api/sponsorships/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/mis-apadrinamientos`.
2. Page loads user's sponsorships via `GET /api/sponsorships/`.
3. Each sponsorship shows animal name, amount, frequency, status badge, and start date.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No sponsorships | Empty state: "No tienes apadrinamientos activos" |
| API loading | Loading spinner |

---

### sponsorship-checkout-submit

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/checkout/apadrinamiento` |
| **API endpoints** | `POST /api/sponsorships/create/`, `POST /api/payments/create-intent/` |

**Preconditions:** User is authenticated with `adopter` role.

**Steps:**

1. User navigates to `/checkout/apadrinamiento`.
2. Page renders frequency selector: Monthly / One-time toggle.
3. User selects frequency.
4. Preset sponsorship amount buttons displayed. User selects preset or enters custom amount.
5. User selects payment method: Tarjeta (card), PSE, or Nequi.
6. Submit button shows selected amount and frequency.
7. User clicks **Submit** button.
8. Frontend sends `POST /api/sponsorships/create/` followed by `POST /api/payments/create-intent/`.
9. Payment provider processes the transaction.
10. User is redirected to `/checkout/confirmacion` with status.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No amount selected | Submit button disabled |
| No payment method selected | Submit button disabled |
| Payment fails | Error message shown |

---

## Favorite Module

### favorite-toggle

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/animales/[id]` |
| **API endpoints** | `POST /api/favorites/toggle/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User is on animal detail page.
2. User clicks the heart/favorite icon.
3. Frontend sends `POST /api/favorites/toggle/` with `{ animal }`.
4. Backend creates or deletes the Favorite record.
5. Heart icon toggles between filled (favorited) and outline (not favorited).

---

### favorite-list

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/favoritos` |
| **API endpoints** | `GET /api/favorites/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/favoritos`.
2. Page loads user's favorited animals via `GET /api/favorites/`.
3. Each favorite shows animal name, species, shelter name.
4. User can click to view animal detail or remove from favorites.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No favorites | Empty state: "No tienes favoritos aún" |

---

## Adopter Intent Module

### adopter-intent-create

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter |
| **Frontend route** | `/mi-intencion` |
| **API endpoints** | `POST /api/adopter-intents/create/`, `GET /api/adopter-intents/me/`, `PATCH /api/adopter-intents/me/` (edit existing intent) |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/mi-intencion`.
2. If intent exists, page loads current intent via `GET /api/adopter-intents/me/`.
3. If no intent, form renders with preferences (JSON), description, visibility fields.
4. User fills or updates form and submits.
5. Frontend sends `POST /api/adopter-intents/create/` with form data.
6. Success message shown.

---

### adopter-intent-browse

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shared |
| **Frontend route** | `/busco-adoptar` |
| **API endpoints** | `GET /api/adopter-intents/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/busco-adoptar`.
2. Page loads public adopter intents via `GET /api/adopter-intents/`.
3. Each intent card shows user name, preferences summary, description, status.
4. Shelter admins can view intents and send invitations.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No public intents | Empty state message |

---

### shelter-invite-send

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shelter_admin |
| **Frontend route** | `/looking-to-adopt` |
| **API endpoints** | `POST /api/shelter-invites/create/` |

**Preconditions:** User is authenticated as `shelter_admin` with a verified shelter.

**Steps:**

1. Shelter admin navigates to `/looking-to-adopt`.
2. Page loads public adopter intents via `GET /api/adopter-intents/`.
3. Admin browses intents and clicks on a profile that matches their shelter.
4. Admin clicks **Invitar** / **Send Invite** button on the adopter intent card.
5. Frontend sends `POST /api/shelter-invites/create/` with `{ adopter_id, shelter_id }`.
6. Success toast shown; invite button disabled for that adopter.
7. Adopter receives in-app notification and email (`shelter_invite_sent` event).

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Shelter not verified | Invite button hidden or disabled |
| Invite already sent to this adopter | Button shows "Invitación enviada" |
| Unauthenticated access | Redirect to `/sign-in` |

---

### shelter-invite-respond

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/shelter-invites/`, `PATCH /api/shelter-invites/[pk]/respond/` |

**Preconditions:** User is authenticated as `adopter` and has at least one pending shelter invite.

**Steps:**

1. Adopter navigates to `/my-profile`.
2. Profile stats banner shows `shelter_invites.pending_count > 0`.
3. Adopter clicks the banner or navigates to the invite management area.
4. Page loads pending invites via `GET /api/shelter-invites/`.
5. Each invite card shows shelter name, shelter city, and action buttons (Accept / Reject).
6. Adopter clicks **Aceptar** (accept) or **Rechazar** (reject).
7. Frontend sends `PATCH /api/shelter-invites/[pk]/respond/` with `{ response: 'accepted' | 'rejected' }`.
8. Invite status updates; pending count decrements.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No pending invites | Banner not shown; invite list shows empty state |
| Unauthenticated access | Redirect to `/sign-in` |
| API error | Error toast; invite remains in pending state |

---

## Adopter Module

### adopter-profile

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/user/profile-stats/`, `GET /api/user/activity/` |

**Preconditions:** User is authenticated as `adopter`.

**Steps:**

1. User navigates to `/my-profile`.
2. Page reads user from auth store; shows loading skeleton until user is available.
3. Left column: profile card (name, role badge, member-since), completeness bar, and activity timeline.
4. Right column: adopter activity cards (applications, donations, sponsorships, favorites, intent, etc.).
5. Banner shown if `shelter_invites.pending_count > 0`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No stats loaded | Activity cards show zero/empty states |
| `adopter_intent` present | Completeness reaches 100% |
| Pending shelter invites | Invite banner rendered above cards |

---

### profile-activity-feed

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter, shelter_admin, web_manager, admin, veterinarian |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/user/activity/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/my-profile`.
2. Page calls `GET /api/user/activity/` on load (via `authStore.fetchActivity`).
3. The recent-activity timeline renders combined events (applications, donations, sponsorships, favorites), most recent first.
4. Each entry shows an icon, label, and relative timestamp.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No activity yet | Empty state message |

---

### shelter-admin-profile

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/user/profile/` (returns `shelter`, `shelter_stats`) |

**Preconditions:** User is authenticated as `shelter_admin`.

**Steps:**

1. User navigates to `/my-profile`.
2. Page reads role from auth store; calls `GET /api/user/profile/` for shelter data.
3. Left column: profile card, completeness bar (name 30 + email 30 + phone 40), pending-applications widget.
4. Right column: `ShelterAdminProfileSection` with shelter details and quick actions.
5. Adopter-only cards (applications, donations, favorites) are NOT rendered.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `pending_applications > 0` | Widget shows count with link to `/shelter/applications` |
| `pending_applications === 0` | Widget shows "No hay solicitudes pendientes" |

---

### admin-profile

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/user/profile/` (returns `admin_stats`) |

**Preconditions:** User is authenticated as `admin`.

**Steps:**

1. User navigates to `/my-profile`.
2. Page reads role; calls `GET /api/user/profile/` for admin stats.
3. Left column: profile card, completeness bar (name 30 + email 30 + phone 40), moderation-queue widget.
4. Right column: `AdminProfileSection` with platform stats and quick actions.
5. Adopter-only cards and activity timeline are NOT rendered.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `pending_verifications > 0` | Widget shows count with link to `/admin/dashboard` |
| `pending_verifications === 0` | Widget shows "No hay refugios pendientes de verificación" |

---

### notification-preferences

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/my-profile/notifications` |
| **API endpoints** | `GET /api/notifications/preferences/`, `PUT /api/notifications/preferences/update/` |

**Preconditions:** User is authenticated with `adopter` role.

**Steps:**

1. User navigates to `/my-profile/notifications`.
2. Page loads notification preferences from `GET /api/notifications/preferences/`.
3. Preferences display toggle switches for each notification event group (email, in-app channels).
4. User toggles a preference switch.
5. Frontend sends `PUT /api/notifications/preferences/update/` with updated preferences.
6. Success confirmation shown.

---

## Shelter Panel Module

### shelter-panel-dashboard

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/dashboard` |
| **API endpoints** | `GET /api/shelters/` |

**Preconditions:** User is authenticated as shelter_admin and owns a shelter.

**Steps:**

1. User navigates to `/refugio/dashboard`.
2. Page loads shelter info and displays verification status badge.
3. Navigation cards to: Animales, Solicitudes, Campañas, Donaciones, Configuración.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No shelter registered | Message + link to `/refugio/onboarding` |
| Shelter pending | Amber "Pendiente de verificación" badge |
| Shelter verified | Green "Verificado" badge |

---

### shelter-panel-animals

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/animales` |
| **API endpoints** | `GET /api/animals/`, `POST /api/animals/create/`, `PATCH /api/animals/<id>/update/`, `DELETE /api/animals/<id>/delete/` |

**Preconditions:** User is authenticated as shelter_admin.

**Steps:**

1. Shelter admin navigates to `/refugio/animales`.
2. Page loads shelter's animals list with status filters.
3. Admin can create new animals, edit existing ones, or change status (draft → published → archived).
4. Each animal card shows name, species, status badge, and action buttons.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No animals | Empty state + "Agregar animal" CTA |
| Filters applied | List updates with filtered results |

---

### shelter-panel-animal-create

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shelter_admin |
| **Frontend route** | `/shelter/animals` (create modal or inline form) |
| **API endpoints** | `POST /api/animals/create/` |

**Preconditions:** User is authenticated as `shelter_admin` with an owned shelter.

**Steps:**

1. Shelter admin navigates to `/shelter/animals`.
2. Admin clicks **Agregar animal** / **Add animal** button.
3. Create form (modal or page) renders with required fields: name, species, breed, age, gender, status, description.
4. Admin fills all required fields and optionally uploads photos.
5. Admin clicks **Guardar** / **Save**.
6. Frontend sends `POST /api/animals/create/` with form data.
7. New animal appears in the list with status `draft`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Missing required fields | Inline validation errors; submit blocked |
| API error | Error toast; form stays open |
| Animal saved as `published` | Immediately visible on public `/animals` page |

---

### shelter-panel-animal-edit

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shelter_admin |
| **Frontend route** | `/shelter/animals` (edit form) |
| **API endpoints** | `GET /api/animals/[pk]/`, `PATCH /api/animals/[pk]/update/` |

**Preconditions:** User is authenticated as `shelter_admin`; at least one animal exists.

**Steps:**

1. Shelter admin navigates to `/shelter/animals`.
2. Admin clicks the edit action on an animal card.
3. Edit form opens pre-populated with existing animal data.
4. Admin modifies one or more fields (description, photos, health info, status).
5. Admin clicks **Guardar** / **Save**.
6. Frontend sends `PATCH /api/animals/[pk]/update/` with changed fields.
7. Animal card in the list reflects the updated data.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No changes made | Save button disabled or no-op |
| API error | Error toast; form stays open with original values |
| Status changed to `published` | Animal becomes visible on public listing |

---

### shelter-panel-animal-archive

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | shelter_admin |
| **Frontend route** | `/shelter/animals` |
| **API endpoints** | `DELETE /api/animals/[pk]/delete/` |

**Preconditions:** User is authenticated as `shelter_admin`; at least one active animal exists.

**Steps:**

1. Shelter admin navigates to `/shelter/animals`.
2. Admin clicks the archive/delete action on an animal card.
3. Confirmation dialog appears: "¿Archivar este animal?" with Cancel and Confirm buttons.
4. Admin clicks **Confirmar**.
5. Frontend sends `DELETE /api/animals/[pk]/delete/` (soft-delete via `archived_at`).
6. Animal disappears from the active list.
7. Archived animal no longer appears on the public `/animals` page.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Admin clicks Cancel | Dialog closes; animal unchanged |
| Animal has pending adoption applications | Warning shown (animal can still be archived) |
| API error | Error toast; animal remains in list |

---

### shelter-panel-campaigns

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/campanas` |
| **API endpoints** | `GET /api/campaigns/`, `POST /api/campaigns/create/`, `PATCH /api/campaigns/<id>/update/` |

**Preconditions:** User is authenticated as shelter_admin.

**Steps:**

1. Shelter admin navigates to `/refugio/campanas`.
2. Page loads shelter's campaigns with progress bars.
3. Admin can create new campaigns or update existing ones.
4. Each campaign shows title, status, goal, raised amount, and progress.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No campaigns | Empty state + "Crear campaña" CTA |

---

### shelter-panel-donations

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/donaciones` |
| **API endpoints** | `GET /api/donations/` |

**Preconditions:** User is authenticated as shelter_admin.

**Steps:**

1. Shelter admin navigates to `/refugio/donaciones`.
2. Page loads donations received by the shelter.
3. Each donation shows donor (anonymized or email), amount, status, campaign (if any), and date.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No donations | Empty state message |

---

### shelter-panel-settings

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/configuracion` |
| **API endpoints** | `GET /api/shelters/<id>/`, `PATCH /api/shelters/<id>/update/` |

**Preconditions:** User is authenticated as shelter_admin and owns a shelter.

**Steps:**

1. Shelter admin navigates to `/refugio/configuracion`.
2. Page loads current shelter info.
3. Form displays: name, legal name, description, city, address, phone, email, website.
4. Admin edits fields and submits.
5. Shelter info updates and success message shown.

---

### shelter-panel-applications

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/solicitudes` |
| **API endpoints** | `GET /api/adoptions/`, `PUT /api/adoptions/<id>/status/` |

**Preconditions:** User is authenticated with `shelter_admin` role. Shelter has received adoption applications.

**Steps:**

1. Shelter admin navigates to `/refugio/solicitudes`.
2. Page loads applications for the shelter from `GET /api/adoptions/`.
3. Each application card shows applicant email, animal name, status badge, submission date.
4. Admin clicks status action buttons: **Revisar** → **Entrevista** → **Aprobar** / **Rechazar**.
5. Frontend sends `PUT /api/adoptions/<id>/status/` with `{ status }`.
6. Application status updates in the list.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No applications | Empty state message shown |
| Status already final (approved/rejected) | No further action buttons |

---

### shelter-panel-updates

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/updates` |
| **API endpoints** | `GET /api/updates/`, `DELETE /api/updates/<id>/delete/` |

**Preconditions:** User is authenticated with `shelter_admin` role.

**Steps:**

1. Shelter admin navigates to `/refugio/updates`.
2. Page loads update posts from `GET /api/updates/`.
3. Each post card shows title, content preview, creation date.
4. Admin can click **Create** button to navigate to `/refugio/updates/create`.
5. Admin can delete a post by clicking delete action.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No update posts | Empty state message shown |

---

### shelter-panel-update-create

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/updates/create` |
| **API endpoints** | `POST /api/updates/create/` |

**Preconditions:** User is authenticated with `shelter_admin` role.

**Steps:**

1. Shelter admin navigates to `/refugio/updates/create`.
2. Form renders: title, content, optional campaign/animal association, image upload.
3. Admin fills form fields.
4. Admin clicks **Publish** / **Submit** button.
5. Frontend sends `POST /api/updates/create/` with form data.
6. Backend creates update post (HTTP 201).
7. Redirect to `/refugio/updates`.

---

### shelter-panel-campaign-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/campanas/[id]` |
| **API endpoints** | `GET /api/campaigns/<id>/`, `PATCH /api/campaigns/<id>/update/`, `POST /api/campaigns/<id>/submit-for-approval/` |

**Preconditions:** User is authenticated as shelter_admin and owns the campaign.

**Steps:**

1. Shelter admin navigates to `/refugio/campanas/[id]`.
2. Page loads campaign info: title, goal, approval status badge.
3. If `approval_status` is `pending` or `rejected`, an **Edit** button appears.
4. Admin clicks **Edit** → inline form renders with title, description, goal fields.
5. Admin saves changes → `PATCH /api/campaigns/<id>/update/` sent; editing mode exits.
6. If campaign was `rejected`, a **Reenviar a revisión** button also appears.
7. Admin clicks **Reenviar** → `POST /api/campaigns/<id>/submit-for-approval/` sent; status updates.
8. `CampaignMessageThread` renders below the detail section showing back-and-forth with the web manager.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `approval_status = approved` | Edit and Reenviar buttons hidden |
| `approval_status = rejected` | Both Edit and Reenviar visible |
| Save fails | Error surfaced; edit form stays open |

---

### shelter-panel-campaign-create

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/refugio/campanas/nueva` |
| **API endpoints** | `GET /api/shelters/?owner=me`, `POST /api/campaigns/create/` |

**Preconditions:** User is authenticated as shelter_admin and owns a shelter.

**Steps:**

1. Shelter admin navigates to `/refugio/campanas/nueva`.
2. Page auto-fetches the admin's shelter ID via `GET /api/shelters/?owner=me`.
3. Form renders: Title (ES), Title (EN, optional), Description (ES), Description (EN, optional), Goal (COP).
4. Admin fills required fields (title and goal) and clicks **Enviar para revisión**.
5. Frontend sends `POST /api/campaigns/create/` with `{ shelter, title_es, title_en, description_es, description_en, goal_amount, status: 'draft' }`.
6. On success → redirect to `/refugio/campanas/[newId]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Title or goal missing | Client validation error; no API call |
| No shelter found | Error: "No encontramos tu refugio" |

---

## Admin Module

### shelter-panel-campaign-messages

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shelter_admin |
| **Frontend route** | `/shelter/campaigns/[id]` |
| **API endpoints** | `GET /api/campaigns/[pk]/messages/`, `POST /api/campaigns/[pk]/messages/` |

**Preconditions:** Shelter admin is authenticated and owns a campaign under review.

**Steps:**

1. Shelter admin navigates to `/shelter/campaigns/[id]`.
2. The `CampaignMessageThread` loads existing messages via `GET /api/campaigns/[pk]/messages/`.
3. Admin types a message in the compose textarea coordinating the approval.
4. Admin clicks "Enviar".
5. Frontend sends `POST /api/campaigns/[pk]/messages/`; the new message appends to the thread.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Empty message body | Send does nothing / no request |
| No prior messages | Empty thread with compose box |

---

### admin-dashboard

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | admin |
| **Frontend route** | `/admin/dashboard` |
| **API endpoints** | `GET /api/admin/dashboard/` |

**Preconditions:** User is authenticated with `role=admin`.

**Steps:**

1. User navigates to `/admin/dashboard`.
2. Page loads platform metrics (users, shelters, animals, applications, campaigns, donations, sponsorships).
3. Quick action links to: Aprobar Refugios, Moderación, Auditoría de Pagos, Métricas.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Not admin | "Acceso denegado" message |

---

### admin-approve-shelters

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | admin |
| **Frontend route** | `/admin/refugios/aprobar` |
| **API endpoints** | `GET /api/admin/shelters/pending/`, `POST /api/admin/shelters/approve/<id>/` |

**Preconditions:** User is authenticated with `role=admin`.

**Steps:**

1. Page loads pending shelters list.
2. Each shelter shows name, legal_name, city, owner email, registration date.
3. Admin clicks **Aprobar** or **Rechazar**.
4. Frontend sends `POST /api/admin/shelters/approve/<id>/` with `{ action: 'approve' | 'reject' }`.
5. Shelter removed from pending list.

---

### admin-moderation

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/moderacion` |
| **API endpoints** | `GET /api/animals/`, `GET /api/campaigns/`, `GET /api/updates/` |

**Preconditions:** User is authenticated with `role=admin`.

**Steps:**

1. Admin navigates to `/admin/moderacion`.
2. Page loads recently published animals, campaigns, and update posts.
3. Admin can review content and take action (archive, unpublish).

---

### admin-metrics

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/metricas` |
| **API endpoints** | `GET /api/admin/metrics/` |

**Preconditions:** User is authenticated with `role=admin`.

**Steps:**

1. Admin navigates to `/admin/metricas`.
2. Page loads detailed financial and adoption metrics.
3. Displays: total donations, total sponsorships, adoption success rate, shelters by status, animals by status.

---

### admin-payments

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/pagos` |
| **API endpoints** | `GET /api/payments/` (placeholder) |

**Preconditions:** User is authenticated with `role=admin`.

**Steps:**

1. Admin navigates to `/admin/pagos`.
2. Page loads payment audit table.
3. Each row shows payment ID, provider reference, amount, status, donor, date.
4. Placeholder note: "Wompi integration pending — displaying mock data."

---

## Navigation Module

### navigation-header

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | all pages |

**Steps:**

1. Header renders on every page. Desktop layout activates at `lg:` (1024px); below that the hamburger drawer is shown.
2. Contains logo/brand linking to `/`.
3. Navigation links: Animales, Refugios, Campañas, Busco Adoptar, Blog, Nosotros dropdown (Quiénes Somos, Trabaja con Nosotros, Aliados Estratégicos).
4. Unauthenticated: Sign In and Sign Up links.
5. Authenticated — **Panel dropdown** (role-specific): shelter_admin opens "Panel Refugio" (7 items: Dashboard, Animales, Solicitudes, Campañas, Donaciones, Actualizaciones, Ajustes); web_manager opens "Panel Web Manager" (3 items: Solicitudes, Refugios, Campañas); admin opens "Admin" (6 items: Dashboard, Aprobar refugios, Moderación, Pagos, Métricas, Blog); veterinarian gets a direct link to "Panel Veterinario".
6. Authenticated — **Avatar/Account dropdown**: Mi Perfil, Favoritos, Mis solicitudes, Mis donaciones, Mis apadrinamientos, Notificaciones, Manual (all authenticated roles — content is filtered per role inside the page), Cerrar sesión.
7. Mobile (`< lg:`): bell icon beside hamburger links to /my-profile/notifications (with unread badge); drawer contains Panel section and Mi cuenta section.

---

### navigation-footer

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | all pages |

**Steps:**

1. Footer renders on every page.
2. Contains columns: Explore (Animales, Refugios, Campañas), Account (Sign In, Sign Up), Info (FAQ).
3. Copyright and branding.

---

### navigation-between-pages

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | all pages |

**Steps:**

1. User navigates between pages via header links, CTAs, and card links.
2. URL updates correctly in browser address bar.
3. Browser back/forward buttons work as expected.
4. Pages render without full-page reload (client-side navigation).

---

### notification-bell

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter, shelter_admin, web_manager, admin, veterinarian |
| **Frontend route** | all pages |
| **API endpoints** | `GET /api/notifications/unread-count/`, `GET /api/notifications/logs/`, `PUT /api/notifications/logs/mark-all-read/` |

**Preconditions:** User is authenticated.

**Steps:**

1. Authenticated user sees bell icon in header.
2. Bell displays unread count badge (polled every 30 seconds).
3. User clicks bell icon to open notification dropdown.
4. Dropdown shows up to 10 recent notifications.
5. User clicks **Mark all as read** button.
6. Frontend sends `PUT /api/notifications/logs/mark-all-read/`.
7. Unread count resets to 0, badge disappears.
8. User can click **View all notifications** link to navigate to full notifications page.

---

### notification-mark-all-read

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter, shelter_admin, web_manager, admin, veterinarian |
| **Frontend route** | all pages (header notification bell) |
| **API endpoints** | `GET /api/notifications/logs/`, `GET /api/notifications/unread-count/`, `POST /api/notifications/logs/mark-all-read/` |

**Preconditions:** User is authenticated and has at least one unread notification.

**Steps:**

1. User clicks the notification bell in the header.
2. The dropdown opens; the "mark all read" control renders while `unreadCount > 0`.
3. User clicks "mark all read".
4. Frontend sends `POST /api/notifications/logs/mark-all-read/`.
5. The unread badge clears and listed notifications render as read.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No unread notifications | "mark all read" control is not shown |

---

### locale-switch

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | all pages |

**Preconditions:** None.

**Steps:**

1. User sees ES/EN locale switcher in header.
2. Current locale is highlighted (default: ES).
3. User clicks the alternate locale toggle.
4. Page content re-renders in the target language without full page reload.
5. URL updates to reflect new locale prefix (e.g., `/es/animales` → `/en/animales`).
6. Locale preference persists across navigation.

---

## Public Module

### public-faq

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/faq` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/faq`.
2. Page renders FAQ accordion with questions and answers.
3. User can expand/collapse individual questions.

---

### public-contact

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/contactanos` |
| **API endpoints** | `GET /api/google-captcha/site-key/`, `POST /api/contact/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/contactanos`.
2. Page renders heading (e.g. Contáctanos), contact form fields, and WhatsApp section.
3. User may submit the form; client requests site key for reCAPTCHA when needed, then `POST /api/contact/` with the message payload.
4. On success, UI shows a confirmation state.

**E2E traceability:** [`frontend/e2e/public/contact.spec.ts`](../frontend/e2e/public/contact.spec.ts).

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| API error | Inline or toast error; user remains on page |

---

### public-about

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/about` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/about`.
2. Page renders organization information and mission statement.

---

### public-terms

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/terms` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/terms`.
2. Page renders terms of service content.

---

### public-work-with-us

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/work-with-us` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/work-with-us`.
2. Page renders volunteer and work opportunities information.

---

### public-strategic-allies

| Field | Value |
|-------|-------|
| **Priority** | P4 |
| **Roles** | shared |
| **Frontend route** | `/strategic-allies` |
| **API endpoints** | `GET /api/strategic-allies/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/strategic-allies`.
2. Page loads partner organizations from `GET /api/strategic-allies/`.
3. Each ally card shows name, logo, and website link.

---

## Blog Module

### blog-browse

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/blog` |
| **API endpoints** | `GET /api/blog/` |

**Preconditions:** None.

**Steps:**

1. User navigates to `/blog`.
2. Page renders featured post card (large) and regular post grid.
3. Search bar allows client-side filtering by title/excerpt.
4. Category filter buttons filter posts by category.
5. Pagination with Previous/Next buttons navigates between pages.
6. User clicks a blog post card to navigate to `/blog/[slug]`.

---

### blog-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/blog/[slug]` |
| **API endpoints** | `GET /api/blog/<slug>/` |

**Preconditions:** Blog post with given slug exists and is published.

**Steps:**

1. Desde el listado del blog, el usuario abre la tarjeta del artículo.
2. Page renders full article with title, content, author, reading time, date.
3. Reading progress bar tracks scroll position.
4. Back link returns user to blog listing.


**HTML editorial sin contenido estructurado:** se muestra después del saneamiento; conserva texto, formato, imágenes y enlaces seguros. Se eliminan eventos, protocolos ejecutables y contenido activo. Si el saneamiento falla, no se inserta HTML original. Outcomes: `display`, `failure`.

---

## Blog Admin Module

### blog-admin-list

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/blog` |
| **API endpoints** | `GET /api/blog/admin/` |

**Preconditions:** User is authenticated with `admin` role.

**Steps:**

1. Admin navigates to `/admin/blog`.
2. Page lists all blog posts (published, draft, scheduled) with status indicators.
3. Links to **Nuevo Post** (create) and **Calendario** (calendar view).
4. Each post row has edit/delete actions.

---

### blog-admin-create

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/blog/crear` |
| **API endpoints** | `POST /api/blog/admin/create/` |

**Preconditions:** User is authenticated with `admin` role.

**Steps:**

1. Admin navigates to `/admin/blog/crear`.
2. Page shows Manual and JSON import tabs.
3. Manual tab: form with title (ES/EN), slug, content, category, cover image, SEO fields.
4. JSON import tab: paste JSON content for bulk creation.
5. Admin fills form and clicks **Publish** / **Save as Draft**.
6. Frontend sends `POST /api/blog/admin/create/` with form data.
7. Blog post created, redirect to admin blog list.

---

### blog-admin-edit

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/blog/[id]/editar` |
| **API endpoints** | `GET /api/blog/admin/<id>/`, `PUT /api/blog/admin/<id>/update/` |

**Preconditions:** User is authenticated with `admin` role. Blog post with given ID exists.

**Steps:**

1. Admin navigates to `/admin/blog/[id]/editar`.
2. Form loads existing post data: title, content, JSON content, SEO fields, cover image.
3. Admin edits fields.
4. Admin clicks **Update** / **Save**.
5. Frontend sends `PUT /api/blog/admin/<id>/update/` with updated data.
6. Blog post updated, success message shown.

---

### blog-admin-calendar

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | admin |
| **Frontend route** | `/admin/blog/calendario` |
| **API endpoints** | `GET /api/blog/admin/calendar/` |

**Preconditions:** User is authenticated with `admin` role.

**Steps:**

1. Admin navigates to `/admin/blog/calendario`.
2. Calendar view renders monthly overview with post indicators.
3. Posts color-coded by status (published, draft, scheduled).
4. Navigation arrows allow moving between months.
5. Clicking a day/post navigates to the edit page.

---

## Volunteer Module

### volunteer-apply

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/work-with-us/apply/[positionId]` |
| **API endpoints** | `GET /api/volunteer-positions/`, `POST /api/volunteer-applications/` |

**Preconditions:** User navigated from `/work-with-us` page. Volunteer position with given ID exists and is active.

**Steps:**

1. User navigates to `/work-with-us` and sees available volunteer positions.
2. User clicks **Apply** on a position card.
3. Browser navigates to `/work-with-us/apply/[positionId]`.
4. Application form renders with fields: name, email, phone, motivation, availability.
5. User fills out the form and completes reCAPTCHA verification.
6. User clicks **Submit**.
7. Frontend sends `POST /api/volunteer-applications/` with form data.
8. On success: confirmation message displayed, email notification sent to admin.
9. On validation error: field-level errors displayed inline.

**Branching:**

- If position is no longer active → show "position unavailable" message.
- If reCAPTCHA fails → submit button remains disabled.

---

### profile-edit

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/my-profile/edit` |
| **API endpoints** | `GET /api/user/profile/`, `PATCH /api/user/profile/` |

**Preconditions:** User is authenticated.

**Steps:**

1. User navigates to `/my-profile` and clicks **Edit Profile** button.
2. Browser navigates to `/my-profile/edit`.
3. Form loads with current profile data (name, phone, city); role-specific sections rendered for shelter_admin and admin. Avatar upload is deferred (Phase 13b).
4. User modifies fields.
5. User clicks **Save**.
6. Frontend sends `PATCH /api/user/profile/` with updated fields.
7. On success: redirected to `/my-profile` with updated data visible.
8. On validation error: field-level errors displayed inline.

**Branching:**

- If user navigates directly to `/my-profile/edit` without auth → redirected to `/sign-in`.

---

### favorites-compare

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter |
| **Frontend route** | `/favorites` |
| **API endpoints** | `GET /api/favorites/`, `GET /api/animals/<id>/` |

**Preconditions:** User is authenticated and has at least 2 favorited animals.

**Steps:**

1. User navigates to `/favorites`.
2. Favorites list renders with animal cards showing enriched data.
3. User selects 2+ animals using comparison checkboxes.
4. User clicks **Compare** button.
5. Comparison modal/panel opens showing side-by-side attributes (species, size, age, energy level, behavioral traits).
6. User reviews differences and closes comparison.

**Branching:**

- If fewer than 2 animals selected → Compare button disabled.
- If no favorites exist → empty state with CTA to browse animals.

---

### blog-admin-delete

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | admin |
| **Frontend route** | `/admin/blog` |
| **API endpoints** | `DELETE /api/blog/admin/<id>/delete/` |

**Preconditions:** User is authenticated with `admin` role. At least one blog post exists.

**Steps:**

1. Admin navigates to `/admin/blog`.
2. Blog list renders with post rows containing action buttons.
3. Admin clicks **Eliminar** on a post.
4. Confirmation dialog appears: "¿Eliminar [title]? Esta acción no se puede deshacer."
5. Admin clicks **Eliminar** to confirm.
6. Frontend sends `DELETE /api/blog/admin/<id>/delete/`.
7. Post removed from list, page refreshes.

**Branching:**

- If admin clicks **Cancelar** → dialog closes, no deletion.

---

### blog-admin-duplicate

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | admin |
| **Frontend route** | `/admin/blog` |
| **API endpoints** | `POST /api/blog/admin/<id>/duplicate/` |

**Preconditions:** User is authenticated with `admin` role. At least one blog post exists.

**Steps:**

1. Admin navigates to `/admin/blog`.
2. Blog list renders with post rows containing action buttons.
3. Admin clicks **Duplicar** on a post.
4. Confirmation dialog appears: "¿Duplicar [title]?"
5. Admin clicks **Duplicar** to confirm.
6. Frontend sends `POST /api/blog/admin/<id>/duplicate/`.
7. New draft post created, list refreshes showing the duplicate.

**Branching:**

- If admin clicks **Cancelar** → dialog closes, no duplication.

---

### favorite-note-edit

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter |
| **Frontend route** | `/favorites` |
| **API endpoints** | `PATCH /api/favorites/<id>/` |

**Preconditions:** User is authenticated and has at least one favorited animal.

**Steps:**

1. User navigates to `/favorites`.
2. Favorites list renders with animal cards.
3. User clicks the note icon (sticky note) on a favorite card.
4. Textarea expands inline below the card.
5. User types or edits the note text.
6. After 500ms debounce, frontend sends `PATCH /api/favorites/<id>/` with updated note.
7. Note persists on reload.

**Branching:**

- If note is empty → note icon appears in muted style.
- If note has content → note icon appears in teal with truncated preview.

---

### adoption-application-history

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter |
| **Frontend route** | `/my-applications/[id]/history` |
| **API endpoints** | `GET /api/adoptions/<id>/`, `GET /api/animals/<pk>/clinical-history/` |

**Preconditions:** User is authenticated with `adopter` role. Adoption application exists for the user.

**Steps:**

1. User navigates to `/my-applications`.
2. User clicks a specific application card to open `/my-applications/[id]/history`.
3. Page fetches adoption application details from `GET /api/adoptions/<id>/`.
4. Page heading shows the animal's name.
5. Page fetches clinical history from `GET /api/animals/<pk>/clinical-history/`.
6. `ClinicalHistoryTimeline` renders each entry with title, type badge, date, and body in the active locale.
7. If no entries, shows "No hay entradas clínicas registradas." empty state.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No clinical entries | Empty state text shown |
| API error | Page renders empty silently |
| Not authenticated | Redirected to `/sign-in` via `useRequireAuth` |

---

## Veterinarian Module

### vet-follow-ups-list

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | veterinarian |
| **Frontend route** | `/veterinarian/follow-ups` |
| **API endpoints** | `GET /api/follow-ups/` |

**Preconditions:** User is authenticated with `role=veterinarian`. At least one follow-up is assigned to them.

**Steps:**

1. User navigates to `/veterinarian/follow-ups`.
2. Layout gate checks `role=veterinarian`; non-vets are redirected.
3. Page fetches assigned follow-ups from `GET /api/follow-ups/`.
4. Each card shows animal name, scheduled date, adopter name, and status badge (pending/in_progress/completed/overdue).
5. User clicks a card to navigate to `/veterinarian/follow-ups/[id]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No assigned follow-ups | Empty state shown |
| Role ≠ veterinarian | Redirect to `/` |

---

### vet-follow-up-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | veterinarian |
| **Frontend route** | `/veterinarian/follow-ups/[id]` |
| **API endpoints** | `GET /api/follow-ups/<id>/`, `POST /api/animals/<pk>/clinical-history/`, `PATCH /api/follow-ups/<id>/complete/` |

**Preconditions:** User is authenticated with `role=veterinarian`. Follow-up is assigned to them.

**Steps:**

1. User navigates to `/veterinarian/follow-ups/[id]`.
2. Page fetches follow-up detail from `GET /api/follow-ups/<id>/` (includes embedded `clinical_entries`).
3. Header shows animal name, scheduled date, and current status.
4. **Mark complete** button visible when `status !== 'completed'`.
5. `ClinicalHistoryTimeline` renders existing clinical entries.
6. `ClinicalEntryForm` is rendered below the timeline.
7. User fills the form (title, entry type, body_es, body_en) and clicks **Guardar entrada**.
8. Frontend sends `POST /api/animals/<pk>/clinical-history/` with `{ follow_up: id, ... }`.
9. New entry appears at the top of the timeline.
10. User optionally clicks **Mark complete** → `PATCH /api/follow-ups/<id>/complete/` is sent.
11. Status updates to `completed`; the Mark complete button disappears.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Follow-up already `completed` | Mark complete button hidden |
| API error on entry save | Error remains in form; store's `addEntry` propagates the rejection |

---

## Web Manager Module

### web-manager-shelters

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/shelters` |
| **API endpoints** | `GET /api/admin/shelters/all/` |

**Preconditions:** User is authenticated with `role=web_manager` or `admin`.

**Steps:**

1. User navigates to `/web-manager/shelters`.
2. Layout gate permits only `web_manager` and `admin` roles.
3. Page fetches shelters from `GET /api/admin/shelters/all/` with optional `verification_status` filter.
4. Filter chips (Todos / Verificado / Pendiente / Rechazado) appear at the top.
5. Paginated shelter cards list with name, city, verification badge.
6. User clicks a shelter card to navigate to `/web-manager/shelters/[id]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No shelters match filter | Empty state shown |
| Role not authorized | Redirect to `/` |

---

### web-manager-shelter-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/shelters/[id]` |
| **API endpoints** | `GET /api/shelters/<id>/`, `GET /api/admin/shelters/<id>/applications/` |

**Preconditions:** User is authenticated with `role=web_manager` or `admin`. Shelter exists.

**Steps:**

1. User navigates to `/web-manager/shelters/[id]`.
2. Page renders two tabs: **Info** and **Applications**.
3. **Info** tab: shelter name, city, verification status, owner email, description.
4. User clicks **Applications** tab.
5. `AdminApplicationsTable` renders applications scoped to this shelter from `GET /api/admin/shelters/<id>/applications/`.
6. Each row shows applicant email, animal name, status badge, and submission date.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No applications for shelter | Empty state shown in table |

---

### web-manager-applications

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/applications` |
| **API endpoints** | `GET /api/admin/applications/` |

**Preconditions:** User is authenticated with `role=web_manager` or `admin`.

**Steps:**

1. User navigates to `/web-manager/applications`.
2. Page fetches all applications from `GET /api/admin/applications/` (paginated).
3. Status filter chips (Todos / submitted / reviewing / approved / rejected) at top.
4. `AdminApplicationsTable` renders all results.
5. User clicks a status chip → query param `status` updates and table refetches.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No applications | Empty state shown |
| Filter applied with no matches | Empty state shown |

---

### web-manager-campaigns

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/campaigns` |
| **API endpoints** | `GET /api/admin/campaigns/` (with `approval_status` filter) |

**Preconditions:** User is authenticated with `role=web_manager` or `admin`.

**Steps:**

1. User navigates to `/web-manager/campaigns`.
2. Layout gate permits only `web_manager` and `admin` roles.
3. Page fetches campaigns from the API with `approval_status` filter (default: `pending`).
4. Filter tabs (Pendientes / Aprobadas / Rechazadas / Todas) appear at the top.
5. Paginated campaign cards list with title, shelter name, goal, and approval status.
6. A **Nueva campaña** button links to `/web-manager/campaigns/new`.
7. User clicks a campaign card to navigate to `/web-manager/campaigns/[id]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| No campaigns in selected tab | "No hay campañas en este estado" empty state |
| Role not authorized | Redirect to `/` |

---

### web-manager-campaign-detail

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/campaigns/[id]` |
| **API endpoints** | `GET /api/campaigns/<id>/`, `POST /api/admin/campaigns/<id>/approve/`, `POST /api/admin/campaigns/<id>/reject/` |

**Preconditions:** User is authenticated with `role=web_manager` or `admin`. Campaign exists.

**Steps:**

1. User navigates to `/web-manager/campaigns/[id]`.
2. Page fetches campaign detail; renders title, shelter name, goal, approval status badge.
3. If `approval_status = pending`, **Aprobar** and **Rechazar** buttons are shown.
4. User clicks **Aprobar** → `POST /api/admin/campaigns/<id>/approve/` sent; status badge updates to `approved`.
5. Alternatively, user clicks **Rechazar** → rejection reason textarea expands.
6. User enters reason and clicks **Confirmar rechazo** → `POST /api/admin/campaigns/<id>/reject/` sent with reason; status updates to `rejected`.
7. `CampaignMessageThread` renders below for back-and-forth with the shelter admin.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| `approval_status` not `pending` | Approve/Reject buttons hidden |
| Reject reason empty | Confirm button disabled |

---

### web-manager-campaign-create

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/campaigns/new` |
| **API endpoints** | `GET /api/admin/shelters/all/`, `POST /api/campaigns/create/` |

**Preconditions:** User is authenticated with `role=web_manager` or `admin`.

**Steps:**

1. User navigates to `/web-manager/campaigns/new`.
2. Page auto-fetches the full shelter list for the dropdown.
3. Form renders: Shelter selector (required), Title ES (required), Title EN, Description ES, Description EN, Goal (COP, required).
4. User fills required fields and clicks **Crear campaña**.
5. Frontend sends `POST /api/campaigns/create/` with `{ shelter, title_es, title_en, ... , status: 'draft' }`.
6. Campaigns created by web manager are auto-approved.
7. On success → redirect to `/web-manager/campaigns/[newId]`.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Shelter, title, or goal missing | Client validation error; no API call |

---

## Manual Module

### web-manager-campaign-messages

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | web_manager, admin |
| **Frontend route** | `/web-manager/campaigns/[id]` |
| **API endpoints** | `GET /api/campaigns/[pk]/messages/`, `POST /api/campaigns/[pk]/messages/` |

**Preconditions:** Web manager or admin is authenticated and reviewing a campaign.

**Steps:**

1. Web manager navigates to `/web-manager/campaigns/[id]`.
2. The `CampaignMessageThread` loads existing messages via `GET /api/campaigns/[pk]/messages/`.
3. Reviewer types a message stating what the shelter needs to fix for approval.
4. Reviewer clicks "Enviar".
5. Frontend sends `POST /api/campaigns/[pk]/messages/`; the message appends to the thread.

**Branching conditions:**

| Condition | Behavior |
|-----------|----------|
| Empty message body | Send does nothing / no request |

---

### Ecosistema del manual (2026-09-19)

**Ruta:** `/{locale}/manual/ecosystem`. **Fuentes:** `frontend/lib/manual/ecosystemCatalog.ts`,
`frontend/components/manual/ecosystem/`, `frontend/lib/manual/useEcosystemNavigation.ts`.
Catálogo estático de 69 pantallas, 33 módulos y 7 espacios, contrastado con las páginas
reales de App Router; no consume endpoints de negocio.

#### Roles

Todos los usuarios autenticados exploran el catálogo completo. Describir un módulo
no concede permisos: sólo se ofrece el enlace de entrada cuando su guard de rol lo
permite, y la pantalla/API de destino conserva su propia autorización.

#### Convenciones

- Entrada normal: menú de cuenta → Manual de usuario → Explorar el ecosistema
  (también desde el índice del manual). Los tests parten de Inicio, abren el menú
  de cuenta/móvil y siguen el enlace visible del manual; no sustituyen el catálogo
  ni sus componentes.
- Escritorio desde 1280 px: órbita; por debajo: tarjetas. Ambos comparten la misma
  jerarquía, selección, búsqueda, panel de contexto y recorridos.
- `node`, `tour` y `relations` viven en la URL; un valor desconocido vuelve a un
  estado válido. La rotación/zoom son estado local de presentación.
- Las pantallas de detalle enlazan al listado para elegir un registro real; no hay
  IDs inventados. Los pagos indican modo demostración; el acceso `admin-login`
  es un traspaso técnico sin enlace ejecutable.
- Las instrucciones del manual mantienen su filtro por audiencia, aun cuando
  el mapa muestra módulos ajenos al rol actual.
- Pausa de animación con movimiento reducido, foco, hover, recorrido activo,
  pestaña oculta o escenario fuera de pantalla; listeners/RAF se limpian al salir.

#### Interacciones por vista y resultado

| Flow ID | Inicio → acción → resultado observable | Clase | Rol |
|---|---|---|---|
| `manual-ecosystem-browse` | Todos los roles entran desde el manual y consultan los siete espacios con sus pantallas. | display | 5 roles |
| `manual-ecosystem-navigate` | Seleccionar un espacio, módulo y pantalla; volver al nivel anterior. | success | 5 roles |
| `manual-ecosystem-search` | Buscar un módulo por su nombre o descripción y seleccionarlo. | success | 5 roles |
| `manual-ecosystem-search-empty` | Buscar un término sin coincidencias y ver el estado vacío. | display | 5 roles |
| `manual-ecosystem-tour` | Iniciar un recorrido, avanzar o volver entre módulos y terminar o salir. | success | 5 roles |
| `manual-ecosystem-relations` | Ocultar o mostrar las conexiones operativas del nivel actual. | success | 5 roles |
| `manual-ecosystem-share` | Recargar el enlace del módulo seleccionado y recuperar su contexto. | success | 5 roles |
| `manual-ecosystem-share-invalid` | Abrir un enlace con nodo o recorrido desconocido y volver a una selección válida. | error | 5 roles |
| `manual-ecosystem-access` | Un adoptante consulta un módulo administrativo y ve su audiencia sin un enlace de acceso. | display | adopter |
| `manual-ecosystem-guide` | Volver desde el mapa a la guía conservando el filtro de procesos por rol. | success | 5 roles |
| `manual-ecosystem-auth` | Un visitante sin sesión recibe la redirección al inicio de sesión. | error | guest |
| `manual-ecosystem-orbit` | Ajustar la órbita mediante teclado, arrastre, zoom, centrado y pausa. | success | 5 roles |
| `manual-ecosystem-responsive` | Navegar por tarjetas en 412, 835 y 1195 px sin desbordamiento horizontal. | success | 5 roles |
| `manual-ecosystem-locale` | Entrar desde el manual inglés y consultar un módulo en ese idioma. | display | 5 roles |

**Análisis de las cuatro clases:** `success`: selección, controles y recorridos;
`error`: sesión ausente y URL inválida; `display`: catálogo, contexto, búsqueda
vacía y traducciones. `failure`: **n/a**, el explorador no envía formularios ni
peticiones de negocio; los fallos de autenticación y de las pantallas enlazadas
pertenecen a sus flujos existentes. No se inventan fallos HTTP del catálogo estático.

#### Adoptante

Puede explorar los 7 espacios, incluso administración. En `admin-metrics` ve
descripción y audiencia, sin enlace de entrada; al volver a la guía conserva
sólo los procesos públicos/transversales y de adoptante.

#### Administrador de refugio

Mismo mapa completo; enlaces de gestión de su refugio y pantallas compartidas.
El mapa no habilita gestión de otros refugios ni permisos globales.

#### Veterinario

Mismo mapa completo; acceso al listado de seguimientos y sus fichas a través
de registros reales. Recorrido del espacio veterinario con dos paradas.

#### Web manager

Mismo mapa completo; accesos de coordinación y pantallas compartidas, sin
convertir la visibilidad del mapa en permiso de administración.

#### Administrador

Mismo mapa completo; accesos administrativos y los permisos que ya reconocen
los guards actuales. No se asume acceso al panel de refugio por ser admin.

#### Visitante sin sesión

Salir de la cuenta → abrir nuevamente el explorador → redirección a
`/{locale}/sign-in`, sin renderizar el catálogo.

#### E2E Coverage Index — ecosistema

- `frontend/e2e/app/manual-ecosystem.spec.ts`: entrada, niveles, buscador,
  estado vacío, tour, relaciones, URL/recarga, restricciones, salida de sesión,
  vuelta al manual, enlace real, teclado/arrastre/zoom/pausa.
- `frontend/e2e/app/manual-ecosystem-responsive.spec.ts`: los cinco roles,
  412/835/1195 px sin overflow y navegación en inglés.
- Fixtures sólo en el límite HTTP/autenticación (`helpers/ecosystem-session.ts`);
  sin login real, seed, mutaciones de base de datos ni cambios de permisos.
- Unidad: integridad de rutas, destinos, textos ES/EN, relaciones y procesos;
  reglas de acceso, estado compartible, contexto, búsqueda y controles del tour.

**Auditoría del alcance (2026-09-19):** 14/14 flujos calificados (8 `success`,
2 `error`, 4 `display`), sin `junk-only` ni faltantes; `failure` n/a por la
razón anterior. Freshness y sincronización de tags correctas. Quality Gate
estricto de los tests nuevos: 100/100, sin errores, warnings ni excepciones.
El barrido estático del repo conserva 12 exenciones existentes y 7 tests sin tag
fuera de este alcance; no equivale a ejecutar toda la suite.

---

### manual-browse

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | all authenticated (adopter, shelter_admin, admin, veterinarian, web_manager) |
| **Frontend route** | `/manual` |
| **API endpoints** | None (static content) |

**Preconditions:** User is authenticated (any role). Unauthenticated users are redirected to `/sign-in`.

**Steps:**

1. User navigates to `/manual`.
2. Layout calls `useRequireAuth()`. Unauthenticated → redirected to `/sign-in`. Authenticated → content rendered.
3. `filterByRole(user.role)` determines which of the 9 sections are visible. web_manager / admin see all sections; other roles see their subset.
4. Page renders a sticky search bar (Fuse.js, Cmd/Ctrl+K shortcut) and a collapsible sidebar with the visible sections.
5. User expands a section in the sidebar and clicks a process anchor link.
6. Page scrolls smoothly to the `ProcessCard` with that `id`; a teal ring highlights the card for 1.6 s.

**Branches / error cases:**

| Condition | Outcome |
|-----------|---------|
| Unauthenticated | `useRequireAuth` redirects to `/sign-in` |
| Role = adopter | Sees getting-started + adopter sections; staff sections hidden |
| Role = web_manager / admin | Full manual rendered (all 9 sections) |

---

### manual-search

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | all authenticated (adopter, shelter_admin, admin, veterinarian, web_manager) |
| **Frontend route** | `/manual` |
| **API endpoints** | None (client-side Fuse.js index) |

**Preconditions:** Manual page is loaded by any authenticated user.

**Steps:**

1. User types a query into the search input (or presses Cmd/Ctrl+K to focus it).
2. `useManualSearch` runs Fuse.js fuzzy search over the role-filtered sections (title 0.5, keywords 0.25, summary 0.15, steps 0.07). Results respect the user's role-filtered section visibility.
3. Dropdown appears with up to 12 ranked results showing title, role badge, summary snippet, and route.
4. User navigates with ↑/↓ keys; highlighted result changes.
5. User presses Enter (or clicks a result): dropdown closes, page scrolls to the matching `ProcessCard`, ring highlight fires.
6. User presses Esc: query clears and input loses focus.

**Branches / error cases:**

| Condition | Outcome |
|-----------|---------|
| Query produces no matches | "Sin resultados" / "No results" shown in dropdown |
| Query is cleared | Dropdown disappears; `isSearching = false` |
| Multiple rapid keystrokes | `useDeferredValue` defers re-indexing; UI stays responsive |

---

### manual-role-filter

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | adopter, shelter_admin, veterinarian |
| **Frontend route** | `/manual` |
| **API endpoints** | None |

**Preconditions:** User is authenticated as a non-staff role.

**Steps:**

1. User with role `adopter`, `shelter_admin`, or `veterinarian` navigates to `/manual`.
2. `filterManualSectionsForRole(user.role)` runs, returning only sections relevant to that role.
3. Sidebar shows only the filtered sections (e.g., adopter sees `getting-started`, `public-views`, `adopter`; staff sections like `web-manager` are absent).
4. Page body renders only the visible sections and their `ProcessCard` entries.
5. Search index is built from the filtered sections — staff-only processes do not appear in results.

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| Role = web_manager / admin | `filterByRole` returns all sections — no filtering |
| Role = veterinarian | Sees getting-started, public-views, vet sections |
| Role = shelter_admin | Sees getting-started, public-views, shelter, cross-cutting |

---

### web-manager-profile

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | web_manager |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/user/profile/`, `GET /api/user/activity/` |

**Preconditions:** User is authenticated as web_manager.

**Steps:**

1. Web manager navigates to `/my-profile`.
2. Page renders common profile elements: avatar (initials), user full name (h1), role badge, profile completeness bar, Edit Profile button.
3. Profile fields displayed: email, role (`web_manager`), phone (if set), city (if set).
4. Activity timeline rendered with role-specific events: `campaign_reviewed` (campaigns the manager reviewed).
5. Right column heading: "Responsabilidades del web manager".
6. `WebManagerProfileSection` renders: 3 stat cards (pending shelters, submitted applications, pending campaigns — fetched via 3 parallel API calls) and 4 quick action links (shelters, applications, campaigns, new campaign).
7. Cross-links grid below: notifications, FAQ, terms.

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| Unauthenticated access | Redirected to `/sign-in` |
| API fetch fails | Stat cards show em-dash (—) |

---

### veterinarian-profile

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Roles** | veterinarian |
| **Frontend route** | `/my-profile` |
| **API endpoints** | `GET /api/user/profile/`, `GET /api/user/activity/` |

**Preconditions:** User is authenticated as veterinarian.

**Steps:**

1. Veterinarian navigates to `/my-profile`.
2. Page renders common profile elements: avatar (initials), user full name (h1), role badge, profile completeness bar, Edit Profile button.
3. Profile fields displayed: email, role (`veterinarian`), phone (if set), city (if set).
4. Activity timeline rendered with role-specific events: `clinical_entry` (history entries the vet authored) and `followup_completed` (follow-ups they marked complete).
5. Right column heading: "Responsabilidades del veterinario".
6. `VeterinarianProfileSection` renders: 4 stat cards (pending / in_progress / completed / overdue follow-up counts derived from `useFollowUpStore`) and one quick action link to `/veterinarian/follow-ups`.
7. Cross-links grid below: notifications, FAQ, terms.

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| Unauthenticated access | Redirected to `/sign-in` |
| No follow-ups assigned | Empty state message shown below stat cards |

---

## Shelter Application Module

### shelter-application-submit

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | adopter |
| **Frontend route** | `/shelter-application` |
| **API endpoints** | `POST /api/shelter-applications/`, `GET /api/shelter-applications/me/` |

**Preconditions:** User is authenticated as `adopter`. User has no active application (status `submitted` or `under_review`).

**Steps:**

1. Adopter navigates to `/my-profile`.
2. Profile page shows "Postularte como refugio" card as the second adopter activity link.
3. Adopter clicks the card; navigated to `/shelter-application`.
4. Page renders Step 1 — basic shelter data: `shelter_name`, `description_es`, `city`, `address`, `phone`, `email`, `website`.
5. Adopter fills required fields and clicks "Siguiente". Per-step validation fires; missing required fields block advancement.
6. Step 2 renders — legal/fiscal data: `legal_name`, `tax_id`, `legal_representative_name`, `legal_representative_id`.
7. Adopter fills required fields and clicks "Siguiente".
8. Step 3 renders — documents notice (backend `GalleryField` ready; file upload UI deferred).
9. Adopter clicks "Siguiente".
10. Step 4 renders — motivation: `motivation`, `previous_experience`, `capacity_estimate`.
11. Adopter fills required fields and clicks "Enviar postulación".
12. `POST /api/shelter-applications/` is called with the full payload.
13. On 201 response: toast "Postulación enviada" shown, adopter redirected to `/my-profile`.
14. Profile page now shows the "Postularte como refugio" card with status label "Postulación enviada — en cola de revisión".

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| Unauthenticated access | Redirected to `/sign-in` |
| `role !== 'adopter'` | Redirected to `/my-profile` |
| Required field missing | Per-step inline error; "Siguiente" disabled |
| API returns 400 | Error toast displayed |

---

### shelter-application-status

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | adopter |
| **Frontend route** | `/shelter-application` |
| **API endpoints** | `GET /api/shelter-applications/me/` |

**Preconditions:** User is authenticated as `adopter` and has an existing application.

**Steps:**

1. Adopter navigates to `/shelter-application` (or clicks the profile card).
2. `GET /api/shelter-applications/me/` is called; page detects an existing application.
3. Instead of the wizard, a **status view** is rendered.
4. Status `submitted` → informational banner "Tu postulación está en cola de revisión".
5. Status `under_review` → banner "Tu postulación está siendo revisada".
6. Status `approved` → success banner "¡Aprobada! Ya eres administrador de refugio" + CTA to `/shelter/dashboard`.
7. Status `rejected` → rejection reason displayed + "Volver a postular" button (clears state and shows wizard).

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| No existing application | Wizard renders instead of status view |
| `GET /me/` returns 404 | Treated as no application; wizard renders |

---

### shelter-application-review

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | web_manager, admin |
| **Frontend route** | (Django admin `/admin-site/` + API endpoints) |
| **API endpoints** | `GET /api/shelter-applications/`, `GET /api/shelter-applications/<pk>/`, `POST /api/shelter-applications/<pk>/approve/`, `POST /api/shelter-applications/<pk>/reject/` |

**Preconditions:** User is authenticated as `admin` or `web_manager`. At least one application in `submitted` or `under_review` status.

**Steps (approve path):**

1. Reviewer opens Django admin (`/admin-site/`) → `ShelterApplication` list.
2. Sees application in `submitted` status with all 4 data sections visible.
3. Reviewer calls `POST /api/shelter-applications/<pk>/approve/` (or uses admin custom action when implemented).
4. Atomic transaction: new `Shelter` created (name=`shelter_name`, `verification_status=verified`, `verified_at=now()`), `applicant.role` promoted to `shelter_admin`, `created_shelter` linked, application `status` → `approved`.
5. Notification dispatched to applicant (`shelter_application_approved` template).
6. Applicant re-logs in → role is now `shelter_admin` → `/shelter/dashboard` accessible.

**Steps (reject path):**

1. Reviewer calls `POST /api/shelter-applications/<pk>/reject/` with `{ "rejection_reason": "..." }`.
2. Application `status` → `rejected`, `rejection_reason` saved, `reviewed_by` + `reviewed_at` set.
3. Notification dispatched to applicant (`shelter_application_rejected` template).
4. Applicant navigates to `/shelter-application` → sees rejection reason + option to re-apply.

**Branching conditions:**

| Condition | Outcome |
|-----------|---------|
| Application already `approved` or `rejected` | 400 error returned |
| `reject` without `rejection_reason` | 400 validation error |
| Non-admin/web-manager calls approve/reject | 403 Forbidden |

---

## Cross-Reference

| Artifact | Path | Purpose |
|----------|------|---------|
| Flow Definitions (JSON) | `e2e/flow-definitions.json` | Machine-readable flow registry for the E2E reporter |
| Flow Tag Constants | `e2e/helpers/flow-tags.ts` | Reusable tag arrays for Playwright tests |
| E2E Spec Files | `e2e/<module>/*.spec.ts` | Playwright test implementations per module |
| Flow Coverage Report | `e2e-results/flow-coverage.json` | Auto-generated coverage status per flow |
| Architecture Standard | `docs/DJANGO_REACT_ARCHITECTURE_STANDARD.md` | Sections 3.7.5–3.7.10 define the flow methodology |
| E2E Flow Coverage Standard | `docs/E2E_FLOW_COVERAGE_REPORT_STANDARD.md` | Reporter implementation and JSON schema |
| Contract Schemas | `e2e/helpers/contract-schemas.ts` | Backend serializer field definitions for mock validation |
| Contract Validator | `e2e/helpers/contract-validate.ts` | Utility to detect mock/backend schema drift |
| Contract Tests | `e2e/contracts/mock-contract.spec.ts` | CI-runnable contract validation suite |

### Flow ID relationships (deduplication notes)

| Flow IDs | Relationship |
|----------|----------------|
| `adoption-manage` / `shelter-panel-applications` | Misma pantalla de refugio: gestión de solicitudes en `/shelter/applications`. `adoption-manage` enfatiza el dominio “adopción”; `shelter-panel-applications` el panel del refugio. Los E2E deben cubrir la vista y las acciones de estado en esa ruta (ver specs de shelter + adoption). |
| `adoption-track` / `my-applications-list` | Ambos referencian el seguimiento del adoptante en `/my-applications`. `adoption-track` incluye la comprobación de acceso (redirect si no hay sesión); `my-applications-list` cubre el listado autenticado. Un mismo test puede llevar ambos tags `@flow:` cuando aplique. |

### Maintenance Rules

- **Flow IDs must match** across this document, `e2e/flow-definitions.json`, and `e2e/helpers/flow-tags.ts`.
- **Adding a new flow:** Add entry here with full steps/branches, then add to `e2e/flow-definitions.json`, then create E2E tests.
- **Modifying a flow:** Update steps and branches in this document first, then update tests accordingly.
- **Removing a flow:** Remove from this document, `e2e/flow-definitions.json`, and all `@flow:` tags in specs.
- **Bump `Version` and `Last Updated`** on every change.

## Outcome-class migration — Batches 1-3 (auth, animal, donation, sponsorship, adoption, shelter, web-manager, admin)

`frontend/e2e/flow-definitions.json` is migrating from `expectedSpecs` counts to
an `outcomes: [...]` declaration per flow (see `scripts/flow_coverage_audit.py`).
Batch 1 covers the `auth` and `animal` modules (10 of 14 `auth` flows — the four
`expectedSpecs: 0` exemptions are untouched — plus all 4 `animal` flows). Class
conventions: **success** (it works) · **error** (user-correctable rejection) ·
**failure** (system-level: 5xx/network) · **display** (real data reached via UI).
Declare a class only if the app genuinely has that behavior surface — do not
pad, do not shrink what the code shows. Tagging caveat: the audit credits a
class only when the backing test carries a matching `@outcome:` tag (untagged
tests default to `success`) — several auth flows report `partial` from missing
tags on already-good tests; the follow-up worklist lives in the batch-1 QA
record.

**Batch 2 (donation/sponsorship/adoption, 21 flows):** two systematic
corrections vs the heuristic pass — the checkout submit pages are placeholders
today (no real payment call exists from those entry points, so error/failure
there would be unclosable padding), and `adoption-submit` is a plain Link (the
real POST lives in `adoption-form-wizard`). The event-creation modals earned a
genuine three-class declaration (client validation = error, flattened DRF body
vs network fallback = failure). Eight `@outcome:display` tags were added to
existing qualifying tests in the same change (the untagged-defaults-to-success
mechanic). Remaining partials are real untested branches, tracked in the batch
record.

**Batch 3 (shelter/web-manager/admin, 20 flows):** four false greens exposed
(web-manager campaigns/campaign-detail, admin approve-shelters/metrics — each
was `covered` under the single-bucket regime while a declared class had zero
qualifying evidence). Pattern lessons applied: silent catches and optimistic-UI
swallows never earn an `error` class; a `try/finally` with no catch (campaign
approve/reject, message send) is an unhandled rejection, not a failure surface;
distinct failure copy (admin dashboard/metrics `loadError`) DOES earn `failure`.
The display-entry rule is live: display-tagged tests must arrive via UI (one
allow-deep-link escape documented on the shelter video spec, whose listing
navigation is owned by the shelter-detail click test).

**Batch 4 — final (home/navigation/public/blog/blog-admin/campaign/volunteer +
shelter-panel/adopter/favorite/veterinarian/manual/shelter-application/
adopter-intent, 63 flows): the map is now 100% outcome-class migrated — 116
flows carry `outcomes:` and 12 are `exempt`; `expectedSpecs` no longer gates
anything.** Systemic lesson from this batch: an untagged test is credited only
toward `success`, so a flow whose sole class is `display`/`error`/`failure`
reads `missing` even when junk evidence exists — "missing" can silently mean
"junk, mislabeled". The attribution tags added here (~26 `@outcome:display`)
convert those masked states into explicit `junk-only`, which ranks first on the
worklist. Two flows were reclassified `exempt` with `knownGaps` (the
shelter-panel animal-create route never existed; the adopter-intent browse page
is static) — dead surface is not a coverage gap. False greens corrected:
`blog-admin-edit`'s success credit came from a `toHaveURL` that never saves;
`blog-admin-delete` dropped a `failure` class its uncaught delete path cannot
surface; `campaign-updates-feed`'s silent `.catch(() => {})` earns neither
error nor failure. Authoring worklists live in the batch-4 QA record.
