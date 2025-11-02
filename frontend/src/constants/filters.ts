/**
 * Filter constants for dashboard filtering.
 * Following state-management.md specification.
 */

export const STUDENT_STATUSES = ['all', '재학', '졸업', '휴학'] as const;
export const JOURNAL_TIERS = ['all', 'SCIE', 'KCI'] as const;

export type StudentStatus = typeof STUDENT_STATUSES[number];
export type JournalTier = typeof JOURNAL_TIERS[number];
