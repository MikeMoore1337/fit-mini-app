import { describe, expect, it } from 'vitest';

type Rgb = readonly [number, number, number];

function hex(value: string): Rgb {
  const normalized = value.replace('#', '');
  return [0, 2, 4].map((offset) => Number.parseInt(normalized.slice(offset, offset + 2), 16)) as [
    number,
    number,
    number,
  ];
}

function luminance([red, green, blue]: Rgb): number {
  const channels = [red, green, blue].map((channel) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0]! * 0.2126 + channels[1]! * 0.7152 + channels[2]! * 0.0722;
}

function contrast(foreground: string, background: string): number {
  const light = Math.max(luminance(hex(foreground)), luminance(hex(background)));
  const dark = Math.min(luminance(hex(foreground)), luminance(hex(background)));
  return (light + 0.05) / (dark + 0.05);
}

describe('brand color contrast', () => {
  it.each([
    ['light text', '#172018', '#f1f3ec', 4.5],
    ['light muted text', '#657067', '#f1f3ec', 4.5],
    ['light primary', '#ffffff', '#18251d', 4.5],
    ['light secondary', '#172018', '#e8ede4', 4.5],
    ['light link', '#3f5f0e', '#f1f3ec', 4.5],
    ['dark text', '#f2f6ef', '#0d120f', 4.5],
    ['dark muted text', '#aab5ac', '#0d120f', 4.5],
    ['dark primary', '#172018', '#b6f238', 4.5],
    ['dark secondary', '#f2f6ef', '#202a23', 4.5],
    ['dark link', '#b6f238', '#0d120f', 4.5],
    ['light focus ring', '#527613', '#f1f3ec', 3],
    ['dark focus ring', '#b6f238', '#0d120f', 3],
  ])('%s meets the target ratio', (_name, foreground, background, minimum) => {
    expect(contrast(foreground, background)).toBeGreaterThanOrEqual(minimum);
  });
});
