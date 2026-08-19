import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { Exercise, ExerciseGuide } from '../../shared/api/types';
import { Badge, CloseIcon, ErrorState, LoadingState } from '../../shared/ui/common';
import { useModalA11y } from '../../shared/ui/useModalA11y';
import { ExerciseGuideMedia } from './ExerciseGuideMedia';

export function ExerciseGuideDialog({
  exerciseId,
  exerciseTitle,
  exercise,
  onClose,
}: {
  exerciseId: number;
  exerciseTitle: string;
  exercise?: Exercise;
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
              {exercise && (
                <div className="exercise-guide-meta toolbar wrap">
                  <Badge>{exercise.primary_muscle || 'Всё тело'}</Badge>
                  <Badge>{exercise.equipment || 'Без оборудования'}</Badge>
                  <Badge>
                    {
                      {
                        beginner: 'Начальный уровень',
                        intermediate: 'Средний уровень',
                        advanced: 'Продвинутый уровень',
                      }[exercise.difficulty_level]
                    }
                  </Badge>
                </div>
              )}
              {exercise && (
                <section className="exercise-guide-intro" aria-labelledby="guide-purpose">
                  <h3 id="guide-purpose">Для чего это упражнение</h3>
                  <p>
                    Основная задача — нагрузить группу «{exercise.primary_muscle || 'всё тело'}» и
                    выполнить движение с контролируемой техникой. Ниже показаны ключевые фазы и
                    проверенные подсказки.
                  </p>
                </section>
              )}
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
              {!!guide.data.safety_notes?.length && (
                <section className="exercise-guide-section exercise-guide-section--safety">
                  <h3>Что важно для безопасности</h3>
                  <ul>
                    {guide.data.safety_notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </section>
              )}
              {!!guide.data.muscles?.length && (
                <section className="exercise-guide-section" aria-labelledby="guide-muscles">
                  <h3 id="guide-muscles">Какие мышцы работают</h3>
                  <div className="exercise-guide-muscles">
                    {guide.data.muscles.map((muscle) => (
                      <article
                        className="exercise-guide-muscle"
                        key={`${muscle.role_id}-${muscle.name}`}
                      >
                        <div className="exercise-guide-muscle__head">
                          <strong>{muscle.name}</strong>
                          <span>{muscle.role}</span>
                        </div>
                        <p>{muscle.function}</p>
                      </article>
                    ))}
                  </div>
                </section>
              )}
              {!!guide.data.alternatives?.length && (
                <section className="exercise-guide-section">
                  <h3>Проверенные замены</h3>
                  <div className="toolbar wrap">
                    {guide.data.alternatives.map((alternative) => (
                      <Badge key={alternative.id}>{alternative.title}</Badge>
                    ))}
                  </div>
                </section>
              )}
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
