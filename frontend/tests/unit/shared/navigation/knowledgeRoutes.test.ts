import { describe, expect, it } from 'vitest';
import {
  isPublicKnowledgePath,
  publicKnowledgePathFromLegacyRoute,
} from '../../../../src/shared/navigation/knowledgeRoutes';

describe('knowledge route handoff', () => {
  it('maps known legacy app routes to the equivalent public path', () => {
    expect(publicKnowledgePathFromLegacyRoute('/app/knowledge')).toBe('/knowledge');
    expect(
      publicKnowledgePathFromLegacyRoute('/app/knowledge/training/repetitions-in-reserve'),
    ).toBe('/knowledge/training/repetitions-in-reserve');
  });

  it('does not capture unrelated app routes or lookalike prefixes', () => {
    expect(publicKnowledgePathFromLegacyRoute('/app')).toBeNull();
    expect(publicKnowledgePathFromLegacyRoute('/app/knowledgeable')).toBeNull();
    expect(publicKnowledgePathFromLegacyRoute('/app/knowledge-base')).toBeNull();
  });

  it('recognizes only the public knowledge route family', () => {
    expect(isPublicKnowledgePath('/knowledge')).toBe(true);
    expect(isPublicKnowledgePath('/knowledge/nutrition/kbju-as-a-reference')).toBe(true);
    expect(isPublicKnowledgePath('/knowledgeable')).toBe(false);
    expect(isPublicKnowledgePath('/training')).toBe(false);
  });
});
