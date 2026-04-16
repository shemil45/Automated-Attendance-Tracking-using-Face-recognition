/**
 * sessionTime.js
 * ─────────────────────────────────────────────────────────
 * Centralised session time-window logic for AttendNet.
 * Used by the Dashboard to compute real-time session status
 * without duplicating logic across components.
 */

/** How long (in minutes) after a period's start time a session can be opened. */
export const SESSION_WINDOW_MINUTES = 10;

/**
 * Given a period's start time string ("HH:MM"), returns one of three states:
 *   "before_start" — current time is before the period start time
 *   "open"         — current time is within the 10-minute start window
 *   "expired"      — the 10-minute window has closed (or passed entirely)
 *
 * @param {string} startTimeStr  e.g. "08:00"
 * @param {Date}   [now]         Optional reference time (defaults to new Date())
 * @returns {"before_start"|"open"|"expired"}
 */
export function getSessionWindowStatus(startTimeStr, now = new Date()) {
    const [hours, minutes] = startTimeStr.split(':').map(Number);

    // Build today's start and deadline datetime objects
    const start = new Date(now);
    start.setHours(hours, minutes, 0, 0);

    const deadline = new Date(start.getTime() + SESSION_WINDOW_MINUTES * 60 * 1000);

    if (now < start) return 'before_start';
    if (now <= deadline) return 'open';
    return 'expired';
}

/**
 * Returns whether a session can be started right now.
 * When testMode is true, always returns true (bypass).
 *
 * @param {string}  startTimeStr  e.g. "08:00"
 * @param {boolean} testMode
 * @param {Date}    [now]
 * @returns {boolean}
 */
export function canStartSession(startTimeStr, testMode, now = new Date()) {
    if (testMode) return true;
    return getSessionWindowStatus(startTimeStr, now) === 'open';
}
