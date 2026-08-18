import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { ExerciseGuide } from '../../shared/api/types';
import { CloseIcon, ErrorState, LoadingState } from '../../shared/ui/common';
import { useModalA11y } from '../../shared/ui/useModalA11y';
import { ExerciseGuideMedia } from './ExerciseGuideMedia';

export function ExerciseGuideDialog({
  exerciseId,
  exerciseTitle,
  onClose,
}: {
  exerciseId: number;
  exerciseTitle: string;
  onClose: () => void;
}) {
  const [mediaExpanded, setMediaExpanded] = useState(false);
  const panelRef = useModalA11y<HTMLDivElement>(!mediaExpanded, onClose);
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
              <ExerciseGuideMedia items={guide.data.media} onExpandedChange={setMediaExpanded} />
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
              <p className="muted exercise-guide-source">
                Источник:{' '}
                <a href={guide.data.source_url} target="_blank" rel="noreferrer">
                  {guide.data.source_name}
                </a>{' '}
                · {guide.data.source_license}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
