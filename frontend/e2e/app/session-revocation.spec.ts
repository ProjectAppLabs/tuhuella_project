import { test, expect } from '../test-with-coverage';
import {
  AUTH_PROTECTED_REDIRECT,
  AUTH_SESSION_PERSISTENCE,
} from '../helpers/flow-tags';

test('requires fresh login after another session changes the password', {
  tag: [...AUTH_SESSION_PERSISTENCE, ...AUTH_PROTECTED_REDIRECT, '@outcome:success'],
}, async ({ page, request }, testInfo) => {
  const email = `revocation-${Date.now()}-${testInfo.workerIndex}@example.test`;
  const oldPassword = 'OriginalCredentials123!';
  const newPassword = 'ReplacementCredentials456!';
  const registration = await request.post('/api/auth/sign_up/', {
    data: { email, password: oldPassword, terms_accepted: true },
  });
  expect(registration.status()).toBe(201);
  const tokens: { access: string } = await registration.json();

  await page.goto('/es/sign-in?redirect=/my-profile');
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(oldPassword);
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page).toHaveURL(/\/my-profile$/);
  await expect(page.getByText(email, { exact: true })).toBeVisible();

  const passwordChange = await request.post('/api/auth/update_password/', {
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
  await expect(page.getByText(email, { exact: true })).not.toBeVisible();
  await expect(page.getByRole('link', { name: 'Iniciar sesión', exact: true })).toBeVisible();
  // Profile keeps its existing loading state after sign-out. A fresh protected
  // request must reach the proxy without the revoked session's cookies.
  await page.goto('/es/my-profile');
  await expect(page).toHaveURL(/\/sign-in(?:\?|$)/);
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(newPassword);
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page).not.toHaveURL(/\/sign-in/);
  await page.goto('/es/my-profile');
  await expect(page).toHaveURL(/\/my-profile$/);
  await expect(page.getByText(email, { exact: true })).toBeVisible();
});
