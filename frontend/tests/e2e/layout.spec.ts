import { test, expect } from '@playwright/test';

test('homepage layout', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('http://localhost:3000');

  // Wait for the AIZS title to be visible to ensure page loaded
  await expect(page.locator('h1', { hasText: 'AIZS' })).toBeVisible();

  // Ensure the buttons exist
  await expect(page.getByText('图书馆今天几点闭馆？')).toBeVisible();

  await page.screenshot({ path: 'screenshots/homepage.png' });
});
