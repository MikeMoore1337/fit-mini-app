// Canonical YFC production subset from frontend/src/shared/ui/Icon.tsx plus a
// selectively sourced Lucide subset for semantics missing or ambiguous in the
// production pack. No glyphs are drawn here. Sources: THIRD_PARTY_NOTICES.md.
const markup = {
  // Lucide icons, ISC license. Source and notice: THIRD_PARTY_NOTICES.md.
  barcode:
    '<path d="M3 5v14" /><path d="M8 5v14" /><path d="M12 5v14" /><path d="M17 5v14" /><path d="M21 5v14" />',
  bell: '<path d="M10.268 21a2 2 0 0 0 3.464 0" /><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />',
  "coach-invite":
    '<path d="M2 21a8 8 0 0 1 13.292-6" /><circle cx="10" cy="8" r="5" /><path d="M19 16v6" /><path d="M22 19h-6" />',
  check: '<path d="M5 12.5l4.2 4.2L19.5 6.5" />',
  "chevron-down": '<polyline points="5,9 12,16 19,9" />',
  "chevron-right": '<polyline points="9,5 16,12 9,19" />',
  info: '<circle cx="12" cy="12" r="9" /><circle cx="12" cy="7.2" r="0.7" fill="currentColor" stroke="none"/><line x1="12" y1="10.5" x2="12" y2="16.8" /><line x1="10.5" y1="16.8" x2="13.5" y2="16.8" />',
  "more-horizontal":
    '<circle cx="6" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1" fill="currentColor" stroke="none"/>',
  plus: '<line x1="12" y1="4" x2="12" y2="20" /><line x1="4" y1="12" x2="20" y2="12" />',
  timer:
    '<circle cx="12" cy="13" r="7" /><line x1="12" y1="13" x2="15.3" y2="10.5" /><line x1="9.5" y1="3" x2="14.5" y2="3" /><line x1="12" y1="3" x2="12" y2="6" /><path d="M17.5 6.5l1.5-1.5" />',
  "body-weight":
    '<rect x="4" y="5" width="16" height="15" rx="3" /><path d="M8 10a4 4 0 0 1 8 0" /><line x1="12" y1="10" x2="14.2" y2="8.2" /><line x1="8" y1="16" x2="16" y2="16" />',
  "nav-nutrition":
    '<path d="M4 12h16c-.7 5-3.3 8-8 8s-7.3-3-8-8Z" /><path d="M6 12c.4-2.5 2.2-4 4.5-4 1.3 0 2 .4 3 .8 1.2-1.5 2.5-2.3 4.3-2.3" /><path d="M16.2 7.7c.4-1.9 1.6-3.2 3.3-3.7-.1 1.9-1.1 3.2-3.3 3.7Z" /><line x1="7" y1="16" x2="17" y2="16" />',
  "nav-plan":
    '<rect width="8" height="4" x="8" y="2" rx="1" ry="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><path d="M12 11h4" /><path d="M12 16h4" /><path d="M8 11h.01" /><path d="M8 16h.01" />',
  "nav-profile":
    '<circle cx="12" cy="8" r="3.5"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/>',
  "nav-progress":
    '<line x1="4" y1="20" x2="4" y2="13" /><line x1="9" y1="20" x2="9" y2="9" /><line x1="14" y1="20" x2="14" y2="11" /><line x1="19" y1="20" x2="19" y2="5" /><line x1="2.5" y1="20" x2="21.5" y2="20" /><path d="M4 9.5l4-3 4 2 6-5" /><path d="M16.5 3.5H18.8V5.8" />',
  "nav-today":
    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>',
  "shield-check":
    '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" /><path d="m9 12 2 2 4-4" />',
  "sliders-horizontal":
    '<path d="M10 5H3" /><path d="M12 19H3" /><path d="M14 3v4" /><path d="M16 17v4" /><path d="M21 12h-9" /><path d="M21 19h-5" /><path d="M21 5h-7" /><path d="M8 10v4" /><path d="M8 12H3" />',
  "week-cardio":
    '<path d="M12 20s-7-4.4-7-9.2C5 7.5 7 5.5 9.6 5.5c1.2 0 2 .5 2.4 1.4.4-.9 1.2-1.4 2.4-1.4 2.6 0 4.6 2 4.6 5.3C19 15.6 12 20 12 20Z" /><polyline points="7,12 10,12 11.2,9.5 13.3,14.5 14.5,12 17,12" />',
  "week-strength":
    '<line x1="4" y1="9" x2="4" y2="15" /><line x1="7" y1="7" x2="7" y2="17" /><line x1="17" y1="7" x2="17" y2="17" /><line x1="20" y1="9" x2="20" y2="15" /><line x1="7" y1="12" x2="17" y2="12" />',
};

export function icon(name, size = 24) {
  if (!markup[name]) throw new Error(`Unknown approved YFC icon: ${name}`);
  return `<svg class="approved-icon" aria-hidden="true" focusable="false" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${markup[name]}</svg>`;
}
