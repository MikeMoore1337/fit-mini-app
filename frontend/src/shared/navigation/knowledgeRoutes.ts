const LEGACY_KNOWLEDGE_PREFIX = '/app/knowledge';
const PUBLIC_KNOWLEDGE_PREFIX = '/knowledge';

export function isPublicKnowledgePath(path: string): boolean {
  return path === PUBLIC_KNOWLEDGE_PREFIX || path.startsWith(`${PUBLIC_KNOWLEDGE_PREFIX}/`);
}

export function publicKnowledgePathFromLegacyRoute(path: string): string | null {
  if (path === LEGACY_KNOWLEDGE_PREFIX) return PUBLIC_KNOWLEDGE_PREFIX;
  if (!path.startsWith(`${LEGACY_KNOWLEDGE_PREFIX}/`)) return null;
  return path.slice('/app'.length);
}
