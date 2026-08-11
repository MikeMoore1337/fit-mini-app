import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ExerciseGuide } from '../../shared/api/types';
import { ErrorState, LoadingState } from '../../shared/ui/common';
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
  const panelRef = useModalA11y<HTMLDivElement>(true, onClose);
  const guide = useQuery({
    queryKey: ['exercises', exerciseId, 'guide'],
    queryFn: () => api<ExerciseGuide>(`/api/v1/programs/exercises/${exerciseId}/guide`),
  });
  return (
    <div className="modal" role="dialog" aria-modal="true" aria-labelledby="exercise-guide-title">
      <button
        type="button"
        className="modal__backdrop"
        aria-label="Закрыть технику"
        onClick={onClose}
      />
      <div className="modal__panel card exercise-guide-modal__panel" ref={panelRef} tabIndex={-1}>
        <div className="exercise-guide-modal__head">
          <div>
            <span className="eyebrow">Техника упражнения</span>
            <h2 className="modal__title" id="exercise-guide-title">
              {exerciseTitle}
            </h2>
          </div>
          <button className="secondary" aria-label="Закрыть технику" onClick={onClose}>
            ×
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
                {guide.data.images.map((image) => (
                  <figure className="exercise-guide-image" key={image.url}>
                    <div className="exercise-guide-image__frame">
                      <img src={image.url} alt={image.alt} />
                    </div>
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
      </div>
    </div>
  );
}
