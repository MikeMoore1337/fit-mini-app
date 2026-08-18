import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ExerciseGuideMedia } from '../../../../src/features/exercises/ExerciseGuideMedia';
import type { ExerciseGuide } from '../../../../src/shared/api/types';

const media: ExerciseGuide['media'] = [
  {
    type: 'image',
    url: '/static/exercise-guides/bench-press-start.jpg',
    poster: '/static/exercise-guides/bench-press-start.jpg',
    phase: 'Исходное положение',
    alt: 'Жим штанги лёжа: исходное положение',
    source_name: 'free-exercise-db',
    source_url: 'https://example.com/source',
    source_license: 'Unlicense',
    source_license_url: 'https://example.com/license',
    width: 850,
    height: 567,
    byte_size: 72_816,
    sort_order: 0,
  },
  {
    type: 'image',
    url: '/static/exercise-guides/bench-press-active.jpg',
    poster: '/static/exercise-guides/bench-press-active.jpg',
    phase: 'Активная фаза',
    alt: 'Жим штанги лёжа: активная фаза',
    source_name: 'free-exercise-db',
    source_url: 'https://example.com/source',
    source_license: 'Unlicense',
    source_license_url: 'https://example.com/license',
    width: 850,
    height: 567,
    byte_size: 72_202,
    sort_order: 1,
  },
];

afterEach(() => cleanup());

describe('ExerciseGuideMedia', () => {
  it('reserves intrinsic dimensions and lazy-loads static phases', () => {
    render(<ExerciseGuideMedia items={media} />);

    const image = screen.getByAltText('Жим штанги лёжа: исходное положение');
    expect(image).toHaveAttribute('loading', 'lazy');
    expect(image).toHaveAttribute('decoding', 'async');
    expect(image).toHaveAttribute('width', '850');
    expect(image).toHaveAttribute('height', '567');
    expect(image.closest('button')).toHaveStyle({ aspectRatio: '850 / 567' });
  });

  it('shows an accessible static fallback after an asset 404', () => {
    render(<ExerciseGuideMedia items={media} />);

    fireEvent.error(screen.getByAltText('Жим штанги лёжа: исходное положение'));

    expect(
      screen.getByRole('img', { name: 'Жим штанги лёжа: исходное положение' }),
    ).toHaveTextContent('Изображение недоступно');
    expect(screen.queryByRole('button', { name: 'Увеличить: Исходное положение' })).toBeNull();
  });

  it('opens the lightbox on demand and reports its state to the parent modal', () => {
    const onExpandedChange = vi.fn();
    render(<ExerciseGuideMedia items={media} onExpandedChange={onExpandedChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Увеличить: Исходное положение' }));

    expect(
      screen.getByRole('dialog', { name: 'Увеличенное изображение: Исходное положение' }),
    ).toBeInTheDocument();
    expect(onExpandedChange).toHaveBeenCalledWith(true);
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть увеличенное изображение' }));
    expect(onExpandedChange).toHaveBeenLastCalledWith(false);
  });
});
