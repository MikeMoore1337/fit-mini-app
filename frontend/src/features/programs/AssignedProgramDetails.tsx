import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { ApiSchemas } from '../../shared/api/types';
import {
  Badge,
  DisclosureIcon,
  EmptyState,
  ErrorState,
  LoadingState,
} from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { DateInput } from '../../shared/ui/PickerInput';

type ProgramRevision = ApiSchemas['ProgramRevisionResponse'];
type TrainingBlock = ApiSchemas['TrainingBlockResponse'];
type TrainingBlockMutation = ApiSchemas['TrainingBlockMutationResponse'];

const changeLabels: Record<ProgramRevision['change_kind'], string> = {
  assigned: 'Программа назначена',
  program_archived: 'Программа отправлена в архив',
  plan_updated: 'План тренировок изменён',
  block_created: 'Добавлен тренировочный блок',
  block_updated: 'Тренировочный блок изменён',
  block_status_changed: 'Изменён статус тренировочного блока',
};

const actorLabels: Record<ProgramRevision['actor_role'], string> = {
  self: 'Вы',
  trainer: 'Тренер',
  admin: 'Администратор',
  system: 'Система',
};

const blockStatusLabels: Record<TrainingBlock['status'], string> = {
  planned: 'Запланирован',
  active: 'Идёт сейчас',
  completed: 'Завершён',
  archived: 'В архиве',
};

function addDays(value: string, days: number): string {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${value}T12:00:00Z`));
}

export function AssignedProgramDetails({
  programId,
  currentRevisionNumber,
  startDate,
  durationWeeks,
}: {
  programId: number;
  currentRevisionNumber: number;
  startDate: string;
  durationWeeks: number;
}) {
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [mutationRevisionNumber, setMutationRevisionNumber] = useState(currentRevisionNumber);
  const revisionNumber = Math.max(currentRevisionNumber, mutationRevisionNumber);
  const programEndDate = useMemo(
    () => addDays(startDate, Math.max(1, durationWeeks) * 7 - 1),
    [durationWeeks, startDate],
  );
  const [showBlockForm, setShowBlockForm] = useState(false);
  const [blockTitle, setBlockTitle] = useState('Основной блок');
  const [blockStartDate, setBlockStartDate] = useState(startDate);
  const [blockEndDate, setBlockEndDate] = useState(() =>
    addDays(startDate, Math.min(27, Math.max(0, durationWeeks * 7 - 1))),
  );
  const [blockPurpose, setBlockPurpose] = useState('Последовательно выполнять программу');
  const [blockNotes, setBlockNotes] = useState('');
  const [isDeload, setIsDeload] = useState(false);

  const revisions = useQuery({
    queryKey: ['assigned-program', programId, 'revisions'],
    queryFn: () => api<ProgramRevision[]>(`/api/v1/programs/assigned/${programId}/revisions`),
    enabled: expanded,
  });
  const blocks = useQuery({
    queryKey: ['assigned-program', programId, 'blocks'],
    queryFn: () => api<TrainingBlock[]>(`/api/v1/programs/assigned/${programId}/blocks`),
    enabled: expanded,
  });

  const mutation = useMutation({
    mutationFn: ({ blockId, body }: { blockId?: number; body: Record<string, unknown> }) =>
      api<TrainingBlockMutation>(
        blockId
          ? `/api/v1/programs/assigned/${programId}/blocks/${blockId}`
          : `/api/v1/programs/assigned/${programId}/blocks`,
        { method: blockId ? 'PATCH' : 'POST', body },
      ),
    onSuccess: async (result, variables) => {
      setMutationRevisionNumber(result.current_revision_number);
      setShowBlockForm(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['assigned-program', programId] }),
        queryClient.invalidateQueries({ queryKey: ['templates'] }),
        queryClient.invalidateQueries({ queryKey: ['coach', 'programs'] }),
      ]);
      toast(variables.blockId ? 'Статус блока обновлён' : 'Тренировочный блок добавлен');
    },
    onError: (reason) =>
      toast(
        reason instanceof ApiError && reason.status === 409
          ? 'Программа уже изменилась. Обновите данные и повторите действие.'
          : (reason as Error).message,
        'error',
      ),
  });

  const updateBlockStatus = (block: TrainingBlock, status: TrainingBlock['status']) =>
    mutation.mutate({
      blockId: block.id,
      body: {
        expected_revision_number: revisionNumber,
        status,
        reason: `Статус блока «${block.title}» изменён пользователем`,
      },
    });

  return (
    <details
      className="program-advanced compact-disclosure"
      open={expanded}
      onToggle={(event) => setExpanded(event.currentTarget.open)}
    >
      <summary>
        <span>
          <strong>Этапы и история программы</strong>
          <small>Тренировочные блоки и сохранённые изменения · версия {revisionNumber}</small>
        </span>
        <DisclosureIcon />
      </summary>
      <div className="program-advanced__body">
        <section className="program-advanced__section" aria-labelledby={`blocks-${programId}`}>
          <div className="program-advanced__heading">
            <div>
              <h3 id={`blocks-${programId}`}>Тренировочные блоки</h3>
              <p>Периоды с понятной целью внутри текущей программы.</p>
            </div>
            <button
              type="button"
              className="secondary"
              onClick={() => setShowBlockForm((value) => !value)}
            >
              {showBlockForm ? 'Отменить' : 'Добавить блок'}
            </button>
          </div>
          {showBlockForm && (
            <form
              className="program-block-form"
              onSubmit={(event) => {
                event.preventDefault();
                mutation.mutate({
                  body: {
                    expected_revision_number: revisionNumber,
                    title: blockTitle,
                    start_date: blockStartDate,
                    end_date: blockEndDate,
                    purpose: blockPurpose,
                    notes: blockNotes || null,
                    priority_muscle_ids: [],
                    is_deload: isDeload,
                    reason: 'Тренировочный блок добавлен пользователем',
                  },
                });
              }}
            >
              <label className="field program-block-form__wide">
                <span>Название этапа</span>
                <input
                  value={blockTitle}
                  maxLength={128}
                  onChange={(event) => setBlockTitle(event.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Начало</span>
                <DateInput
                  min={startDate}
                  max={programEndDate}
                  value={blockStartDate}
                  onChange={(event) => setBlockStartDate(event.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Окончание</span>
                <DateInput
                  min={blockStartDate}
                  max={programEndDate}
                  value={blockEndDate}
                  onChange={(event) => setBlockEndDate(event.target.value)}
                  required
                />
              </label>
              <label className="field program-block-form__wide">
                <span>Цель этапа</span>
                <input
                  value={blockPurpose}
                  maxLength={500}
                  onChange={(event) => setBlockPurpose(event.target.value)}
                  required
                />
              </label>
              <label className="field program-block-form__wide">
                <span>Заметка (необязательно)</span>
                <textarea
                  value={blockNotes}
                  maxLength={2000}
                  onChange={(event) => setBlockNotes(event.target.value)}
                />
              </label>
              <label className="checkbox-row program-block-form__wide">
                <input
                  type="checkbox"
                  checked={isDeload}
                  onChange={(event) => setIsDeload(event.target.checked)}
                />
                <span>Это облегчённый период со сниженной нагрузкой</span>
              </label>
              <button
                className="program-block-form__wide"
                disabled={mutation.isPending || blockEndDate < blockStartDate}
              >
                {mutation.isPending ? 'Сохраняем…' : 'Сохранить блок'}
              </button>
            </form>
          )}
          {blocks.isLoading ? (
            <LoadingState label="Загружаем этапы…" />
          ) : blocks.error ? (
            <ErrorState
              message={(blocks.error as Error).message}
              retry={() => void blocks.refetch()}
            />
          ) : !blocks.data?.length ? (
            <EmptyState
              title="Блоков пока нет"
              text="Программа работает и без них. Добавьте этап, если хотите зафиксировать период и его цель."
            />
          ) : (
            <div className="program-block-list">
              {blocks.data.map((block) => (
                <article className="program-block" key={block.id}>
                  <div className="program-block__head">
                    <div>
                      <strong>{block.title}</strong>
                      <span>
                        {formatDate(block.start_date)} — {formatDate(block.end_date)}
                      </span>
                    </div>
                    <Badge tone={block.status === 'active' ? 'success' : 'neutral'}>
                      {blockStatusLabels[block.status]}
                    </Badge>
                  </div>
                  <p>{block.purpose}</p>
                  {block.notes && <small>{block.notes}</small>}
                  {block.is_deload && <Badge tone="warning">Облегчённый период</Badge>}
                  {(block.status === 'planned' || block.status === 'active') && (
                    <div className="program-block__actions">
                      {block.status === 'planned' && (
                        <button
                          type="button"
                          className="secondary"
                          disabled={mutation.isPending}
                          onClick={() => updateBlockStatus(block, 'active')}
                        >
                          Начать этап
                        </button>
                      )}
                      {block.status === 'active' && (
                        <button
                          type="button"
                          className="secondary"
                          disabled={mutation.isPending}
                          onClick={() => updateBlockStatus(block, 'completed')}
                        >
                          Завершить этап
                        </button>
                      )}
                      <button
                        type="button"
                        className="text-button"
                        disabled={mutation.isPending}
                        onClick={() => updateBlockStatus(block, 'archived')}
                      >
                        В архив
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
        <section className="program-advanced__section" aria-labelledby={`history-${programId}`}>
          <h3 id={`history-${programId}`}>История изменений</h3>
          {revisions.isLoading ? (
            <LoadingState label="Загружаем историю…" />
          ) : revisions.error ? (
            <ErrorState
              message={(revisions.error as Error).message}
              retry={() => void revisions.refetch()}
            />
          ) : !revisions.data?.length ? (
            <EmptyState title="История появится после первого сохранённого изменения" />
          ) : (
            <ol className="program-revision-list">
              {revisions.data.map((revision) => (
                <li key={revision.id}>
                  <span className="program-revision-list__marker" aria-hidden="true" />
                  <div>
                    <strong>{changeLabels[revision.change_kind]}</strong>
                    <span>
                      {actorLabels[revision.actor_role]} ·{' '}
                      {new Date(revision.created_at).toLocaleString('ru-RU')}
                    </span>
                    {revision.reason && <small>{revision.reason}</small>}
                  </div>
                  <Badge>v{revision.revision_number}</Badge>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </details>
  );
}
