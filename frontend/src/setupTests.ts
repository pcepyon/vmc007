/**
 * Jest setup file for React Testing Library.
 * Extends Jest matchers with RTL custom matchers.
 */

import '@testing-library/jest-dom';

// Set environment variables for tests
process.env.VITE_API_BASE_URL = 'http://localhost:8000';
process.env.VITE_ADMIN_MODE = 'true';
process.env.VITE_ADMIN_API_KEY = 'test-api-key-12345';

// Mock ResizeObserver for Recharts
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Polyfill TextEncoder/TextDecoder for jsdom
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as typeof global.TextDecoder;
