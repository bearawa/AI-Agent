import { test, expect } from '@playwright/test';

test.use({
  video: 'on',
});

test('Admin UI Flow', async ({ page }) => {
  // Navigate to login
  await page.goto('http://localhost:3000/admin');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/admin-login.png', fullPage: true });

  // Wait for the login button to be visible and click it (assuming failure first just to get screenshot)
  const loginButton = page.locator('button', { hasText: 'Sign In' });
  await expect(loginButton).toBeVisible();

  // Test admin dashboard
  await page.goto('http://localhost:3000/admin/dashboard');
  await page.waitForLoadState('networkidle');

  // Wait for the Dashboard title to be visible to ensure content is loaded
  const dashboardTitle = page.locator('h1', { hasText: 'System Dashboard' });
  await expect(dashboardTitle).toBeVisible();

  await page.screenshot({ path: 'screenshots/admin-dashboard.png', fullPage: true });
});
