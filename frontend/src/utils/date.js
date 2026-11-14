/**
 * Date and time formatting utilities
 * Handles UTC ISO strings, naive SQLite timestamps, and local browser timezones.
 */

export function formatTime(isoStr) {
  if (!isoStr) return '';
  try {
    let s = String(isoStr).trim().replace(' ', 'T');
    // If no timezone offset exists, assume UTC
    if (!s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
      s += 'Z';
    }
    const date = new Date(s);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
  } catch {
    return '';
  }
}

export function formatDateTime(isoStr) {
  if (!isoStr) return '';
  try {
    let s = String(isoStr).trim().replace(' ', 'T');
    if (!s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
      s += 'Z';
    }
    const date = new Date(s);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return '';
  }
}
