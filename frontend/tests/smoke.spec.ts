import { test, expect } from '@playwright/test';

test('homepage has correct layout and stream starts', async ({ page }) => {
  await page.goto('/');

  // Should have top bar
  await expect(page.locator('header').getByText('NeonPulse AI')).toBeVisible();

  // Should have watchlist
  await expect(page.locator('h2').filter({ hasText: 'WATCHLIST' })).toBeVisible();

  // Should have chat
  await expect(page.locator('h2').filter({ hasText: 'NEONPULSE COPILOT' })).toBeVisible();

  // Wait for stream to connect (top bar changes to CONNECTED)
  await expect(page.getByText('connected')).toBeVisible({ timeout: 10000 });
});

test('can send chat message', async ({ page }) => {
  await page.goto('/');

  // Wait for stream to connect
  await expect(page.getByText('connected')).toBeVisible({ timeout: 10000 });

  const chatInput = page.getByPlaceholder('Ask NeonPulse to analyze or trade...');
  await chatInput.fill('buy 5 aapl');
  await chatInput.press('Enter');

  // Check if user message appears
  await expect(page.getByText('buy 5 aapl')).toBeVisible();

  // Check if AI responds
  // It might be disabled without a key, so we check for either success or error response
  await expect(page.locator('.whitespace-pre-wrap')).toHaveCount(2, { timeout: 15000 });
});
