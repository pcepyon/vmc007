/**
 * Environment Configuration
 * Provides a unified way to access environment variables
 * Compatible with both Vite (production) and Jest (testing)
 */

// Use import.meta.env for Vite (browser) environment
// Vite will inject these at build time
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  ADMIN_MODE: import.meta.env.VITE_ADMIN_MODE === 'true',
  ADMIN_API_KEY: import.meta.env.VITE_ADMIN_API_KEY || '',
};

/**
 * Helper function to get admin mode status
 */
export const getAdminMode = (): boolean => {
  return ENV.ADMIN_MODE;
};
