import { randomInt } from 'node:crypto';

import { test, expect } from '../test-with-coverage';
import {
  AUTH_PROTECTED_REDIRECT,
  AUTH_SESSION_PERSISTENCE,
} from '../helpers/flow-tags';

test('requires fresh login after another session changes the password', {
  tag: [...AUTH_SESSION_PERSISTENCE, ...AUTH_PROTECTED_REDIRECT, '@outcome:success'],
}, async ({ page, context }, testInfo) => {
  const clientIp = `2001:db8::${Array.from({ length: 4 }, () => randomInt(0x10000).toString(16)).join(':')}`;
  await context.setExtraHTTPHeaders({ 'X-Forwarded-For': clientIp });
  const email = `revocation-${Date.now()}-${testInfo.workerIndex}@example.test`;
  const oldPassword = 'OriginalCredentials123!';
  const newPassword = 'ReplacementCredentials456!';
  const registration = await context.request.post('/api/auth/sign_up/', {
    data: { email, password: oldPassword, terms_accepted: true },
  });
  expect(registration.status()).toBe(201);
  const tokens: { access: string } = await registration.json();

  await page.goto('/es/sign-in?redirect=/my-profile');
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(oldPassword);
  const initialLogin = page.waitForResponse(
    (response) => response.url().endsWith('/auth/sign_in/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  const initialLoginResponse = await initialLogin;
  expect(initialLoginResponse.status()).toBe(200);
  expect((await initialLoginResponse.json()).user.email).toBe(email);
  await expect(page).toHaveURL(/\/my-profile$/);
  const initialValidation = page.waitForResponse(
    (response) => response.url().endsWith('/auth/validate_token/') && response.status() === 200,
  );
  await page.goto('/es/my-profile');
  expect((await (await initialValidation).json()).user.email).toBe(email);
  await expect(page.getByText(email, { exact: true })).toBeVisible();

  const passwordChange = await context.request.post('/api/auth/update_password/', {
    headers: { Authorization: `Bearer ${tokens.access}` },
    data: { current_password: oldPassword, new_password: newPassword },
  });
  expect(passwordChange.status()).toBe(200);
  const accessRejection = page.waitForResponse(
    (response) => response.url().includes('/auth/validate_token/') && response.status() === 401,
  );
  const refreshRejection = page.waitForResponse(
    (response) => response.url().includes('/token/refresh/') && response.status() === 401,
  );

  await page.reload();
  await accessRejection;
  await refreshRejection;
  await expect(page.getByText(email, { exact: true })).toBeHidden();
  await expect(page.getByRole('link', { name: 'Iniciar sesión', exact: true })).toBeVisible();
  // Profile keeps its existing loading state after sign-out. A fresh protected
  // request must reach the proxy without the revoked session's cookies.
  await page.goto('/es/my-profile');
  await expect(page).toHaveURL(/\/sign-in(?:\?|$)/);
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(newPassword);
  const freshLogin = page.waitForResponse(
    (response) => response.url().endsWith('/auth/sign_in/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  const freshLoginResponse = await freshLogin;
  expect(freshLoginResponse.status()).toBe(200);
  expect((await freshLoginResponse.json()).user.email).toBe(email);
  await expect(page).not.toHaveURL(/\/sign-in/);
  const freshValidation = page.waitForResponse(
    (response) => response.url().endsWith('/auth/validate_token/') && response.status() === 200,
  );
  await page.goto('/es/my-profile');
  expect((await (await freshValidation).json()).user.email).toBe(email);
  await expect(page).toHaveURL(/\/my-profile$/);
  await expect(page.getByText(email, { exact: true })).toBeVisible();
});
