import { useEffect, useId, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { CoachAssignedProgram, Exercise, ExerciseGuide } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

const difficultyLabels = {
  beginner: 'Начальный',
  intermediate: 'Средний',
  advanced: 'Продвинутый',
};

export function ExerciseCatalog({
  canCreate = false,
  canAssign = false,
  targetTelegramId,
}: {
  canCreate?: boolean;
  canAssign?: boolean;
  targetTelegramId?: number | null;
}) {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const searchResultsId = useId();
  const [search, setSearch] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [muscle, setMuscle] = useState('');
  const [guide, setGuide] = useState<{ exercise: Exercise; data: ExerciseGuide } | null>(null);
  const [largeImage, setLargeImage] = useState<number | null>(null);
  const [assignment, setAssignment] = useState<Exercise | null>(null);
  const [assignmentClientId, setAssignmentClientId] = useState(0);
  const [assignmentProgramId, setAssignmentProgramId] = useState(0);
  const [assignmentSets, setAssignmentSets] = useState(3);
  const [assignmentReps, setAssignmentReps] = useState('8-12');
  const [assignmentRest, setAssignmentRest] = useState(90);
  const [newTitle, setNewTitle] = useState('');
  const rows = useQuery({
    queryKey: ['exercises'],
    queryFn: () => api<Exercise[]>('/api/v1/programs/exercises'),
  });
  const coachPrograms = useQuery({
    queryKey: ['coach', 'programs'],
    queryFn: () => api<CoachAssignedProgram[]>('/api/v1/coach/assigned-programs'),
    enabled: canAssign,
  });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['exercises'] });
      setNewTitle('');
      toast('Каталог обновлён');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const assignmentMutation = useMutation({
    mutationFn: () => {
      if (!assignment || !activeAssignmentClientId || !activeAssignmentProgramId)
        throw new Error('Выберите клиента и программу');
      return api<{ workouts_updated: number }>(
        `/api/v1/coach/clients/${activeAssignmentClientId}/programs/${activeAssignmentProgramId}/exercises`,
        {
          method: 'POST',
          body: {
            exercise_id: assignment.id,
            prescribed_sets: assignmentSets,
            prescribed_reps: assignmentReps,
            rest_seconds: assignmentRest,
          },
        },
      );
    },
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ['coach', 'programs'] });
      toast(`Упражнение добавлено в ${result.workouts_updated} предстоящих тренировок`);
      setAssignment(null);
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const muscles = useMemo(
    () => [...new Set((rows.data ?? []).map((item) => item.primary_muscle).filter(Boolean))].sort(),
    [rows.data],
  );
  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (rows.data ?? []).filter(
      (item) =>
        (!muscle || item.primary_muscle === muscle) &&
        (!query ||
          `${item.title} ${item.primary_muscle} ${item.equipment}`.toLowerCase().includes(query)),
    );
  }, [rows.data, search, muscle]);
  const assignablePrograms = useMemo(
    () => (coachPrograms.data ?? []).filter((item) => item.is_active && item.workouts_planned > 0),
    [coachPrograms.data],
  );
  const assignmentClients = useMemo(
    () => [
      ...new Map(
        assignablePrograms.map((item) => [
          item.client_id,
          {
            id: item.client_id,
            name:
              item.client_full_name ||
              (item.client_username
                ? `@${item.client_username}`
                : String(item.client_telegram_user_id)),
          },
        ]),
      ).values(),
    ],
    [assignablePrograms],
  );
  const activeAssignmentClientId = assignmentClients.some((item) => item.id === assignmentClientId)
    ? assignmentClientId
    : (assignmentClients[0]?.id ?? 0);
  const clientPrograms = assignablePrograms.filter(
    (item) => item.client_id === activeAssignmentClientId,
  );
  const activeAssignmentProgramId = clientPrograms.some((item) => item.id === assignmentProgramId)
    ? assignmentProgramId
    : (clientPrograms[0]?.id ?? 0);

  useEffect(() => {
    if (!guide && !assignment) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      if (largeImage !== null) setLargeImage(null);
      else if (assignment) setAssignment(null);
      else setGuide(null);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [assignment, guide, largeImage]);

  const openGuide = async (exercise: Exercise) => {
    try {
      const data =
        exercise.guide ??
        (await api<ExerciseGuide>(`/api/v1/programs/exercises/${exercise.id}/guide`));
      setGuide({ exercise, data });
    } catch (reason) {
      toast((reason as Error).message, 'error');
    }
  };

  return (
    <>
      <Card title="Каталог упражнений" actions={<Badge>{filtered.length}</Badge>}>
        <div className="form-grid exercise-filter-grid top-gap">
          <label className="field">
            <span>Поиск</span>
            <div className="exercise-picker">
              <input
                type="search"
                role="combobox"
                aria-label="Поиск в каталоге упражнений"
                aria-expanded={searchOpen}
                aria-controls={searchResultsId}
                autoComplete="off"
                value={search}
                onFocus={() => setSearchOpen(true)}
                onBlur={() => setSearchOpen(false)}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setSearchOpen(true);
                }}
                placeholder="Упражнение, мышца или инвентарь"
              />
              {searchOpen && (
                <div className="exercise-picker__results" id={searchResultsId} role="listbox">
                  {filtered.length ? (
                    filtered.map((exercise) => (
                      <button
                        type="button"
                        role="option"
                        aria-selected={search === exercise.title}
                        className="exercise-picker__option"
                        key={exercise.id}
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => {
                          setSearch(exercise.title);
                          setSearchOpen(false);
                        }}
                      >
                        <strong>{exercise.title}</strong>
                        <span className="exercise-picker__meta">
                          <small>
                            {exercise.primary_muscle || 'Все мышцы'} ·{' '}
                            {exercise.equipment || 'Без оборудования'}
                          </small>
                          <span className="badge">
                            {difficultyLabels[exercise.difficulty_level]}
                          </span>
                        </span>
                      </button>
                    ))
                  ) : (
                    <span className="exercise-picker__empty">Ничего не найдено</span>
                  )}
                </div>
              )}
            </div>
          </label>
          <label className="field">
            <span>Группа мышц</span>
            <select value={muscle} onChange={(e) => setMuscle(e.target.value)}>
              <option value="">Все</option>
              {muscles.map((value) => (
                <option value={value!} key={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>
        {canCreate && (
          <form
            className="toolbar wrap top-gap"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate({
                path: '/api/v1/programs/exercises',
                method: 'POST',
                body: {
                  title: newTitle,
                  difficulty_level: 'intermediate',
                  target_telegram_user_id: targetTelegramId || null,
                },
              });
            }}
          >
            <input
              aria-label="Новое упражнение"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Название нового упражнения"
              required
            />
            <button disabled={mutation.isPending}>Добавить</button>
          </form>
        )}
        {rows.isLoading ? (
          <LoadingState />
        ) : rows.error ? (
          <ErrorState message={(rows.error as Error).message} retry={() => void rows.refetch()} />
        ) : filtered.length === 0 ? (
          <EmptyState title="Ничего не найдено" />
        ) : (
          <div className="list-grid top-gap">
            {filtered.map((exercise) => (
              <article className="list-row exercise-catalog-row" key={exercise.id}>
                <div className="list-row__main">
                  <strong>{exercise.title}</strong>
                  <span className="muted">
                    {exercise.primary_muscle || 'Все мышцы'} ·{' '}
                    {exercise.equipment || 'Без оборудования'}
                  </span>
                  <div className="exercise-catalog-row__badges">
                    <Badge>{difficultyLabels[exercise.difficulty_level]}</Badge>{' '}
                    {exercise.is_custom && <Badge>Своё</Badge>}
                  </div>
                </div>
                <div className="list-row__actions">
                  {canAssign && (
                    <button type="button" onClick={() => setAssignment(exercise)}>
                      Добавить
                    </button>
                  )}
                  {exercise.has_guide && (
                    <button
                      className="secondary"
                      type="button"
                      onClick={() => void openGuide(exercise)}
                    >
                      Техника
                    </button>
                  )}
                  {exercise.is_custom && (
                    <button
                      className="btn-danger"
                      type="button"
                      onClick={async () => {
                        if (
                          await confirm({
                            title: 'Удалить упражнение?',
                            message: exercise.title,
                            confirmText: 'Удалить',
                          })
                        )
                          mutation.mutate({
                            path: `/api/v1/programs/exercises/${exercise.id}`,
                            method: 'DELETE',
                          });
                      }}
                    >
                      Удалить
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </Card>
      {guide && (
        <div
          className="modal exercise-guide-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="guide-title"
        >
          <button className="modal__backdrop" aria-label="Закрыть" onClick={() => setGuide(null)} />
          <div className="modal__panel card exercise-guide-modal__panel">
            <div className="exercise-guide-modal__head">
              <div>
                <span className="eyebrow">Описание упражнения</span>
                <h2 className="modal__title" id="guide-title">
                  {guide.exercise.title}
                </h2>
              </div>
              <button
                className="secondary exercise-guide-modal__close"
                aria-label="Закрыть описание"
                onClick={() => setGuide(null)}
              >
                ×
              </button>
            </div>
            <div className="exercise-guide-modal__body">
              <div className="exercise-guide-meta toolbar wrap">
                <Badge>{difficultyLabels[guide.exercise.difficulty_level]}</Badge>
                <Badge>{guide.exercise.primary_muscle || 'Всё тело'}</Badge>
                <Badge>{guide.exercise.equipment || 'Без оборудования'}</Badge>
              </div>
              <section className="exercise-guide-intro" aria-labelledby="guide-purpose">
                <h3 id="guide-purpose">Для чего это упражнение</h3>
                <p>
                  Основная задача — нагрузить целевую группу «
                  {guide.exercise.primary_muscle || 'всё тело'}» и отработать движение с
                  контролируемой амплитудой. Используйте технику ниже, чтобы направить нагрузку в
                  нужные мышцы и не компенсировать движение корпусом.
                </p>
              </section>
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
                <section className="exercise-guide-note" aria-labelledby="guide-technique">
                  <h3 id="guide-technique">Техника выполнения</h3>
                  <ol>
                    {guide.data.technique_steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>
                <section className="exercise-guide-note" aria-labelledby="guide-breathing">
                  <h3 id="guide-breathing">Дыхание</h3>
                  <p>{guide.data.breathing}</p>
                </section>
                <section
                  className="exercise-guide-note exercise-guide-note--warning"
                  aria-labelledby="guide-mistakes"
                >
                  <h3 id="guide-mistakes">Частые ошибки</h3>
                  <ul>
                    {guide.data.common_mistakes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>
              </div>
              <section className="exercise-guide-section" aria-labelledby="guide-muscles">
                <h3 id="guide-muscles">Какие мышцы работают</h3>
                <div className="exercise-guide-muscles">
                  {guide.data.muscles.map((muscleItem) => (
                    <article className="exercise-guide-muscle" key={muscleItem.name}>
                      <div className="exercise-guide-muscle__head">
                        <strong>{muscleItem.name}</strong>
                        <span>{muscleItem.role}</span>
                      </div>
                      <p>{muscleItem.function}</p>
                    </article>
                  ))}
                </div>
              </section>
              <p className="muted exercise-guide-source">
                Источник:{' '}
                <a href={guide.data.source_url} target="_blank" rel="noreferrer">
                  {guide.data.source_name}
                </a>{' '}
                · {guide.data.source_license}
              </p>
            </div>
            {largeImage !== null && guide.data.images[largeImage] && (
              <div className="exercise-lightbox" role="dialog" aria-modal="true">
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
                  ×
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
                    ‹
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
                    ›
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      {assignment && (
        <div className="modal" role="dialog" aria-modal="true" aria-labelledby="assign-title">
          <button
            className="modal__backdrop"
            aria-label="Закрыть"
            onClick={() => setAssignment(null)}
          />
          <div className="modal__panel card assignment-modal">
            <div className="section-head">
              <div>
                <span className="eyebrow">Назначение упражнения</span>
                <h2 id="assign-title">{assignment.title}</h2>
              </div>
              <button className="secondary" onClick={() => setAssignment(null)}>
                ×
              </button>
            </div>
            {coachPrograms.isLoading ? (
              <LoadingState />
            ) : assignmentClients.length === 0 ? (
              <EmptyState
                title="Нет подходящих программ"
                text="Сначала создайте и назначьте клиенту программу с предстоящими тренировками."
              />
            ) : (
              <form
                className="stack"
                onSubmit={(event) => {
                  event.preventDefault();
                  assignmentMutation.mutate();
                }}
              >
                <label className="field">
                  <span>Кому</span>
                  <select
                    value={activeAssignmentClientId}
                    onChange={(event) => {
                      const nextClientId = Number(event.target.value);
                      setAssignmentClientId(nextClientId);
                      setAssignmentProgramId(
                        assignablePrograms.find((item) => item.client_id === nextClientId)?.id ?? 0,
                      );
                    }}
                  >
                    {assignmentClients.map((client) => (
                      <option value={client.id} key={client.id}>
                        {client.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>В какую программу</span>
                  <select
                    value={activeAssignmentProgramId}
                    onChange={(event) => setAssignmentProgramId(Number(event.target.value))}
                  >
                    {clientPrograms.map((program) => (
                      <option value={program.id} key={program.id}>
                        {program.title}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="muted assignment-modal__hint">
                  Упражнение появится во всех предстоящих тренировках выбранной программы.
                </p>
                <div className="form-grid assignment-prescription">
                  <label className="field">
                    <span>Подходы</span>
                    <input
                      type="number"
                      min="1"
                      max="12"
                      value={assignmentSets}
                      onChange={(event) => setAssignmentSets(Number(event.target.value))}
                    />
                  </label>
                  <label className="field">
                    <span>Повторения</span>
                    <input
                      value={assignmentReps}
                      maxLength={32}
                      onChange={(event) => setAssignmentReps(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    <span>Отдых, сек</span>
                    <input
                      type="number"
                      min="15"
                      max="600"
                      value={assignmentRest}
                      onChange={(event) => setAssignmentRest(Number(event.target.value))}
                    />
                  </label>
                </div>
                <button disabled={assignmentMutation.isPending || !activeAssignmentProgramId}>
                  {assignmentMutation.isPending ? 'Добавляем…' : 'Добавить в программу'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
