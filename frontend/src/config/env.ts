/**
 * Environment Configuration
 * Provides a unified way to access environment variables
 * Compatible with both Vite (production) and Jest (testing)
 */

// Simple approach: always use process.env for consistency
// Vite will inject these at build time
export const ENV = {
  API_BASE_URL: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
  ADMIN_MODE: process.env.VITE_ADMIN_MODE === 'true',
  ADMIN_API_KEY: process.env.VITE_ADMIN_API_KEY || '',
};

/**
 * Helper function to get admin mode status
 */
export const getAdminMode = (): boolean => {
  return ENV.ADMIN_MODE;
};
