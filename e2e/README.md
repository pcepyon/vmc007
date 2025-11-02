# E2E Tests - Playwright

## Running Tests

```bash
# Install dependencies
npm install

# Install Playwright browsers (first time only)
npx playwright install

# Run all tests
npm test

# Run in headed mode (see browser)
npm run test:headed

# Run with UI mode (interactive)
npm run test:ui

# Debug mode
npm run test:debug

# Run specific test file
npx playwright test tests/example.spec.ts

# Run specific browser
npx playwright test --project=chromium
```

## Test Organization

Following test-plan.md: 1% coverage allocation for critical user paths.

### Focus Areas
1. **Happy Path**: Core user scenarios work end-to-end
2. **Empty State**: Graceful handling when no data
3. **Error State**: User-friendly error messages
4. **Filter Functionality**: Dashboard filtering works correctly

### API Mocking

Tests mock backend responses for speed and reliability:

```typescript
// Mock successful response
await page.route('**/api/dashboard', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ data: mockData }),
  });
});

// Mock error response
await page.route('**/api/dashboard', async route => {
  await route.fulfill({
    status: 500,
    body: JSON.stringify({ error: 'Server Error' }),
  });
});
```

## Configuration

### Browser Support
- **Default**: Chromium only (for speed)
- **Optional**: Firefox, WebKit (uncomment in config for cross-browser testing)

### Timeouts
- Test timeout: 30s
- CI retries: 2
- Trace collection: On first retry

### Screenshots
- Captured only on failure
- Saved to `test-results/`

## Best Practices

1. **Use data-testid for stability**
   ```typescript
   await page.locator('[data-testid="metric-card"]').click();
   ```

2. **Wait for network idle**
   ```typescript
   await page.waitForLoadState('networkidle');
   ```

3. **Assert on user-visible content**
   ```typescript
   await expect(page.locator('h1')).toContainText('Dashboard');
   ```

4. **Mock API calls for speed**
   - Don't rely on real backend
   - Control test data precisely
   - Tests run faster and more reliably

## CI/CD Integration

Tests run automatically in CI pipeline:
- Headless mode
- Single worker for stability
- HTML report generated
- Artifacts saved on failure

## Viewing Reports

```bash
# Open HTML report (after test run)
npm run report
```

Report includes:
- Test results with timing
- Screenshots (on failure)
- Traces (on retry)
- Video recordings (if configured)
