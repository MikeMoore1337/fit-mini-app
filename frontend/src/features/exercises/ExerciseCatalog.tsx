import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { Exercise, ExerciseGuide } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

const difficultyLabels = {
  beginner: 'Начальный',
  intermediate: 'Средний',
  advanced: 'Продвинутый',
};

export function ExerciseCatalog({
  canCreate = false,
  targetTelegramId,
}: {
  canCreate?: boolean;
  targetTelegramId?: number | null;
}) {
  const { toast, confirm } = useFeedback();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [muscle, setMuscle] = useState('');
  const [guide, setGuide] = useState<{ exercise: Exercise; data: ExerciseGuide } | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const rows = useQuery({
    queryKey: ['exercises'],
    queryFn: () => api<Exercise[]>('/api/v1/programs/exercises'),
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
        <div className="form-grid top-gap">
          <label className="field">
            <span>Поиск</span>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Упражнение, мышца или инвентарь"
            />
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
              <article className="list-row" key={exercise.id}>
                <div className="list-row__main">
                  <strong>{exercise.title}</strong>
                  <span className="muted">
                    {exercise.primary_muscle || 'Все мышцы'} ·{' '}
                    {exercise.equipment || 'Без оборудования'}
                  </span>
                  <div>
                    <Badge>{difficultyLabels[exercise.difficulty_level]}</Badge>{' '}
                    {exercise.is_custom && <Badge>Своё</Badge>}
                  </div>
                </div>
                <div className="list-row__actions">
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
        <div className="modal" role="dialog" aria-modal="true" aria-labelledby="guide-title">
          <button className="modal__backdrop" aria-label="Закрыть" onClick={() => setGuide(null)} />
          <div className="modal__panel card">
            <div className="section-head">
              <h2 id="guide-title">{guide.exercise.title}</h2>
              <button className="secondary" onClick={() => setGuide(null)}>
                ×
              </button>
            </div>
            <div className="exercise-guide-images top-gap">
              {guide.data.images.map((image) => (
                <figure key={image.url}>
                  <img src={image.url} alt={image.alt} loading="lazy" />
                  <figcaption className="muted">{image.phase}</figcaption>
                </figure>
              ))}
            </div>
            <h3>Техника</h3>
            <ol>
              {guide.data.technique_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <h3>Дыхание</h3>
            <p>{guide.data.breathing}</p>
            <h3>Частые ошибки</h3>
            <ul>
              {guide.data.common_mistakes.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </>
  );
}
