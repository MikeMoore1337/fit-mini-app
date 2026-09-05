import { describe, expect, it } from 'vitest';
import { isPublishedKnowledgePath } from '../../../src/content/publicContent';

describe('public content routing', () => {
  it('recognizes only published knowledge pages from the content manifest', () => {
    expect(isPublishedKnowledgePath('/knowledge')).toBe(true);
    expect(isPublishedKnowledgePath('/knowledge/training/repetitions-in-reserve')).toBe(true);
    expect(isPublishedKnowledgePath('/knowledge/nutrition/glycemic-index')).toBe(true);
    expect(isPublishedKnowledgePath('/knowledge/nutrition/food-sources-for-kbju')).toBe(true);
    expect(isPublishedKnowledgePath('/knowledge/progress/bmi-calculator')).toBe(true);
    expect(isPublishedKnowledgePath('/knowledge/nutrition/hydration-and-water')).toBe(true);
    expect(isPublishedKnowledgePath('/knowledge/unknown-performance-route')).toBe(false);
    expect(isPublishedKnowledgePath('/training')).toBe(false);
  });
});
