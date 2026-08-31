import { useState } from 'react';
import type { ExerciseGuide } from '../../shared/api/types';
import { ChevronIcon, CloseIcon } from '../../shared/ui/common';
import { useModalA11y } from '../../shared/ui/useModalA11y';

type GuideMediaItem = ExerciseGuide['media'][number];

export function ExerciseGuideMedia({
  items,
  onExpandedChange,
}: {
  items: GuideMediaItem[];
  onExpandedChange?: (expanded: boolean) => void;
}) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [failedUrls, setFailedUrls] = useState<Set<string>>(() => new Set());
  const close = () => {
    setExpandedIndex(null);
    onExpandedChange?.(false);
  };
  const lightboxRef = useModalA11y<HTMLDivElement>(expandedIndex !== null, close);
  const activeItem = expandedIndex === null ? null : items[expandedIndex];
  const availableItemsCount = items.filter((item) => !failedUrls.has(item.url)).length;
  const hasStrengthPhases = items.some(
    (item) => item.phase === 'Фаза усилия' || item.phase === 'Фаза возврата',
  );

  const showAdjacent = (direction: -1 | 1) => {
    if (expandedIndex === null) return;
    for (let offset = 1; offset < items.length; offset += 1) {
      const nextIndex = (expandedIndex + direction * offset + items.length) % items.length;
      const nextItem = items[nextIndex];
      if (nextItem && !failedUrls.has(nextItem.url)) {
        setExpandedIndex(nextIndex);
        return;
      }
    }
    close();
  };

  const markFailed = (url: string) => {
    setFailedUrls((current) => new Set(current).add(url));
    if (activeItem?.url === url) close();
  };

  return (
    <>
      {hasStrengthPhases && (
        <p className="exercise-guide-images__legend">
          Изображение показывает положение в конце движения. <strong>Фаза усилия</strong>{' '}
          (концентрическая) — преодоление нагрузки. <strong>Фаза возврата</strong> (эксцентрическая)
          — контролируемое обратное движение.
        </p>
      )}
      <div className="exercise-guide-images" aria-label="Положения упражнения">
        {items.map((item, index) => {
          const failed = failedUrls.has(item.url);
          return (
            <figure className="exercise-guide-image" key={item.url}>
              {failed ? (
                <div
                  className="exercise-guide-image__frame exercise-guide-image__fallback"
                  style={{ aspectRatio: `${item.width} / ${item.height}` }}
                  role="img"
                  aria-label={item.alt}
                >
                  <span aria-hidden="true">Изображение недоступно</span>
                </div>
              ) : (
                <button
                  className="exercise-guide-image__frame"
                  style={{ aspectRatio: `${item.width} / ${item.height}` }}
                  type="button"
                  aria-label={`Увеличить: ${item.phase}`}
                  onClick={() => {
                    setExpandedIndex(index);
                    onExpandedChange?.(true);
                  }}
                >
                  <img
                    src={item.url}
                    alt={item.alt}
                    width={item.width}
                    height={item.height}
                    loading="lazy"
                    decoding="async"
                    onError={() => markFailed(item.url)}
                  />
                  <span className="exercise-guide-image__zoom" aria-hidden="true">
                    ⛶
                  </span>
                </button>
              )}
              <figcaption>{item.phase}</figcaption>
            </figure>
          );
        })}
      </div>
      {activeItem && !failedUrls.has(activeItem.url) && (
        <div
          className="exercise-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={`Увеличенное изображение: ${activeItem.phase}`}
          ref={lightboxRef}
          tabIndex={-1}
        >
          <button
            type="button"
            className="exercise-lightbox__backdrop"
            aria-label="Закрыть увеличенное изображение"
            onClick={close}
          />
          <button
            type="button"
            className="exercise-lightbox__close"
            aria-label="Закрыть"
            onClick={close}
          >
            <CloseIcon />
          </button>
          {availableItemsCount > 1 && (
            <button
              type="button"
              className="exercise-lightbox__arrow exercise-lightbox__arrow--prev"
              aria-label="Предыдущее изображение"
              onClick={() => showAdjacent(-1)}
            >
              <ChevronIcon direction="left" />
            </button>
          )}
          <figure>
            <img
              src={activeItem.url}
              alt={activeItem.alt}
              width={activeItem.width}
              height={activeItem.height}
              decoding="async"
              onError={() => markFailed(activeItem.url)}
            />
            <figcaption>{activeItem.phase}</figcaption>
          </figure>
          {availableItemsCount > 1 && (
            <button
              type="button"
              className="exercise-lightbox__arrow exercise-lightbox__arrow--next"
              aria-label="Следующее изображение"
              onClick={() => showAdjacent(1)}
            >
              <ChevronIcon />
            </button>
          )}
        </div>
      )}
    </>
  );
}
