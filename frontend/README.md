# Frontend - React + TypeScript + Recharts

## Architecture

Following separation of concerns:

```
components/
  ui/                   # Generic UI components (library-agnostic)
  dashboard/            # Chart/widget components (Recharts)
pages/                  # View composition
hooks/                  # State & data handling logic (UI-agnostic)
api/                    # Backend communication
```

## Testing

### Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage

# Update snapshots (if using)
npm test -- -u
```

### Test Organization

- Component tests: `src/components/**/__tests__/*.test.tsx`
- Hook tests: `src/hooks/__tests__/*.test.ts`
- Page tests: `src/pages/__tests__/*.test.tsx`

### Testing Library Philosophy

Tests use React Testing Library following these principles:

1. **Test behavior, not implementation**
2. **Query by accessible roles/text** (what users see)
3. **Avoid testing internal state**
4. **Use user-event for interactions**

Example:
```typescript
// ✅ Good: Testing user-visible behavior
expect(screen.getByText('Total Students')).toBeInTheDocument();
expect(screen.getByTestId('metric-value')).toHaveTextContent('1500');

// ❌ Bad: Testing implementation details
expect(component.state.loading).toBe(false);
```

## Key Components

### Hooks
- `useDashboardData`: Fetch dashboard data from API
- `useDashboardFilter`: Handle filter state with 300ms debouncing (to be implemented)

### UI Components
- `MetricCard`: Display key metrics with optional trend indicators

## Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## API Integration

Vite proxy configuration forwards `/api/*` requests to Django backend (localhost:8000).

```typescript
// Example API call
const response = await fetch('/api/dashboard');
const data = await response.json();
```

## Type Safety

Project uses TypeScript strict mode:
- All props must be typed
- No implicit `any`
- Null checks enforced

## Testing Strategy

Following test-plan.md:
- 4% coverage allocation for frontend hooks
- Focus on data handling logic, not UI styling
- Mock API calls with fetch/axios mock
- Use `waitFor` for async operations
