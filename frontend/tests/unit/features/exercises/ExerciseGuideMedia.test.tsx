import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ExerciseGuideMedia } from '../../../../src/features/exercises/ExerciseGuideMedia';
import type { ExerciseGuide } from '../../../../src/shared/api/types';

const media: ExerciseGuide['media'] = [
  {
    type: 'image',
    url: '/static/exercise-guides/bench-press-start.jpg',
    poster: '/static/exercise-guides/bench-press-start.jpg',
    phase: 'Фаза усилия',
    alt: 'Жим штанги лёжа: фаза усилия',
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
    phase: 'Фаза возврата',
    alt: 'Жим штанги лёжа: фаза возврата',
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

    const image = screen.getByAltText('Жим штанги лёжа: фаза возврата');
    expect(image).toHaveAttribute('loading', 'lazy');
    expect(image).toHaveAttribute('decoding', 'async');
    expect(image).toHaveAttribute('width', '850');
    expect(image).toHaveAttribute('height', '567');
    expect(image.closest('button')).toHaveStyle({ aspectRatio: '850 / 567' });
  });

  it('shows an accessible static fallback after an asset 404', () => {
    render(<ExerciseGuideMedia items={media} />);

    fireEvent.error(screen.getByAltText('Жим штанги лёжа: фаза возврата'));

    expect(screen.getByRole('img', { name: 'Жим штанги лёжа: фаза возврата' })).toHaveTextContent(
      'Изображение недоступно',
    );
    expect(screen.queryByRole('button', { name: 'Увеличить: Фаза возврата' })).toBeNull();
  });

  it('opens the lightbox on demand and reports its state to the parent modal', () => {
    const onExpandedChange = vi.fn();
    render(<ExerciseGuideMedia items={media} onExpandedChange={onExpandedChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Увеличить: Фаза возврата' }));

    expect(
      screen.getByRole('dialog', { name: 'Увеличенное изображение: Фаза возврата' }),
    ).toBeInTheDocument();
    expect(onExpandedChange).toHaveBeenCalledWith(true);
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть увеличенное изображение' }));
    expect(onExpandedChange).toHaveBeenLastCalledWith(false);
  });

  it('explains how strength phases relate to the photographed positions', () => {
    render(<ExerciseGuideMedia items={media} />);

    expect(screen.getByText(/положение в конце движения/)).toBeVisible();
    expect(screen.getByText(/концентрическая/)).toBeVisible();
    expect(screen.getByText(/эксцентрическая/)).toBeVisible();
    expect(screen.getAllByText('Фаза возврата', { exact: true })).toHaveLength(2);
    expect(screen.getAllByText('Фаза усилия', { exact: true })).toHaveLength(2);
  });
});
