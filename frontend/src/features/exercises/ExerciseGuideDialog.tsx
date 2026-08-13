import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ExerciseGuide } from '../../shared/api/types';
import { ChevronIcon, CloseIcon, ErrorState, LoadingState } from '../../shared/ui/common';
import { useModalA11y } from '../../shared/ui/useModalA11y';

export function ExerciseGuideDialog({
  exerciseId,
  exerciseTitle,
  onClose,
}: {
  exerciseId: number;
  exerciseTitle: string;
  onClose: () => void;
}) {
  const [largeImage, setLargeImage] = useState<number | null>(null);
  const panelRef = useModalA11y<HTMLDivElement>(largeImage === null, onClose);
  const lightboxRef = useModalA11y<HTMLDivElement>(largeImage !== null, () => setLargeImage(null));
  const guide = useQuery({
    queryKey: ['exercises', exerciseId, 'guide'],
    queryFn: () => api<ExerciseGuide>(`/api/v1/programs/exercises/${exerciseId}/guide`),
  });
  return (
    <div
      className="modal exercise-guide-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="exercise-guide-title"
    >
      <div className="modal__backdrop" aria-hidden="true" onClick={onClose} />
      <div className="modal__panel card exercise-guide-modal__panel" ref={panelRef} tabIndex={-1}>
        <div className="exercise-guide-modal__head">
          <div>
            <span className="eyebrow">Техника упражнения</span>
            <h2 className="modal__title" id="exercise-guide-title">
              {exerciseTitle}
            </h2>
          </div>
          <button
            type="button"
            className="secondary exercise-guide-modal__close"
            aria-label="Закрыть технику"
            onClick={onClose}
          >
            <CloseIcon />
          </button>
        </div>
        <div className="exercise-guide-modal__body">
          {guide.isLoading && <LoadingState />}
          {guide.error && (
            <ErrorState
              message={(guide.error as Error).message}
              retry={() => void guide.refetch()}
            />
          )}
          {guide.data && (
            <>
              <div className="exercise-guide-images">
                {guide.data.images.map((image, index) => (
                  <figure className="exercise-guide-image" key={image.url}>
                    <button
                      className="exercise-guide-image__frame"
                      type="button"
                      aria-label={`Увеличить: ${image.phase}`}
                      onClick={() => setLargeImage(index)}
                    >
                      <img src={image.url} alt={image.alt} loading="lazy" />
                      <span className="exercise-guide-image__zoom" aria-hidden="true">
                        ⛶
                      </span>
                    </button>
                    <figcaption>{image.phase}</figcaption>
                  </figure>
                ))}
              </div>
              <div className="exercise-guide-notes">
                <section className="exercise-guide-note">
                  <h3>Техника выполнения</h3>
                  <ol>
                    {guide.data.technique_steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>
                <section className="exercise-guide-note">
                  <h3>Дыхание</h3>
                  <p>{guide.data.breathing}</p>
                </section>
                <section className="exercise-guide-note exercise-guide-note--warning">
                  <h3>Частые ошибки</h3>
                  <ul>
                    {guide.data.common_mistakes.map((mistake) => (
                      <li key={mistake}>{mistake}</li>
                    ))}
                  </ul>
                </section>
              </div>
            </>
          )}
        </div>
        {largeImage !== null && guide.data?.images[largeImage] && (
          <div
            className="exercise-lightbox"
            role="dialog"
            aria-modal="true"
            aria-label={`Увеличенное изображение: ${guide.data.images[largeImage].phase}`}
            ref={lightboxRef}
            tabIndex={-1}
          >
            <button
              className="exercise-lightbox__backdrop"
              aria-label="Закрыть увеличенное изображение"
              onClick={() => setLargeImage(null)}
            />
            <button
              type="button"
              className="exercise-lightbox__close"
              aria-label="Закрыть"
              onClick={() => setLargeImage(null)}
            >
              <CloseIcon />
            </button>
            {guide.data.images.length > 1 && (
              <button
                type="button"
                className="exercise-lightbox__arrow exercise-lightbox__arrow--prev"
                aria-label="Предыдущее изображение"
                onClick={() =>
                  setLargeImage(
                    (largeImage - 1 + guide.data.images.length) % guide.data.images.length,
                  )
                }
              >
                <ChevronIcon direction="left" />
              </button>
            )}
            <figure>
              <img
                src={guide.data.images[largeImage].url}
                alt={guide.data.images[largeImage].alt}
              />
              <figcaption>{guide.data.images[largeImage].phase}</figcaption>
            </figure>
            {guide.data.images.length > 1 && (
              <button
                type="button"
                className="exercise-lightbox__arrow exercise-lightbox__arrow--next"
                aria-label="Следующее изображение"
                onClick={() => setLargeImage((largeImage + 1) % guide.data.images.length)}
              >
                <ChevronIcon />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
