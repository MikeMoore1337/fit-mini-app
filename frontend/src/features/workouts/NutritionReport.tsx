import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { api, apiFile } from '../../shared/api/client';
import type { NutritionReport, NutritionReportPeriod } from '../../shared/api/types';
import { dateInputValue, formatCalendarDate } from '../../shared/dateTime';
import { AppLink } from '../../shared/navigation/router';
import { queryKeys } from '../../shared/queryKeys';
import { DateInput } from '../../shared/ui/PickerInput';
import { NUTRITION_WEEK_LEGEND, WeekStrip, type WeekStripDayMeta } from '../../shared/ui/WeekStrip';
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  LoadingState,
  SegmentedControl,
} from '../../shared/ui/common';

const reportPeriods = [
  { value: 'days_7', label: '7 дней' },
  { value: 'days_30', label: '30 дней' },
  { value: 'days_90', label: '90 дней' },
  { value: 'current_week', label: 'Эта неделя' },
  { value: 'current_month', label: 'Этот месяц' },
  { value: 'previous_month', label: 'Прошлый месяц' },
  { value: 'custom', label: 'Свой период' },
] as const;

const reportPeriodSet = new Set<NutritionReportPeriod>(reportPeriods.map((option) => option.value));

type DailyPoint = NutritionReport['daily'][number];
type MetricSummary = NutritionReport['summary']['calories'];
type TargetComparison = NutritionReport['summary']['calorie_comparison'];

const statusLabels: Record<DailyPoint['status'], string> = {
  complete: 'Заполнен',
  incomplete: 'Не завершён',
  fasted: 'Без приёмов пищи',
  missing: 'Нет данных',
};

const targetSourceLabels: Record<NutritionReport['target_changes'][number]['source'], string> = {
  calculated: 'Расчётная цель',
  manual: 'Ручная цель',
  trainer: 'Цель тренера',
  adaptive: 'Принятая адаптация',
};

function initialReportState(): {
  period: NutritionReportPeriod;
  dateFrom: string;
  dateTo: string;
} {
  const params = new URLSearchParams(window.location.search);
  const candidate = params.get('nutrition_period') as NutritionReportPeriod | null;
  const period = candidate && reportPeriodSet.has(candidate) ? candidate : 'days_30';
  const dateFrom = params.get('nutrition_from') ?? '';
  const dateTo = params.get('nutrition_to') ?? '';
  if (period === 'custom' && (!dateFrom || !dateTo)) {
    return { period: 'days_30', dateFrom: '', dateTo: '' };
  }
  return { period, dateFrom, dateTo };
}

function reportPath(
  period: NutritionReportPeriod,
  dateFrom: string,
  dateTo: string,
  csv = false,
  clientId?: number,
): string {
  const params = new URLSearchParams({ period });
  if (period === 'custom') {
    params.set('date_from', dateFrom);
    params.set('date_to', dateTo);
  }
  const base =
    clientId == null
      ? '/api/v1/workouts/progress/nutrition-report'
      : `/api/v1/coach/clients/${clientId}/nutrition-report`;
  return `${base}${csv ? '.csv' : ''}?${params}`;
}

function syncReportUrl(period: NutritionReportPeriod, dateFrom: string, dateTo: string): void {
  const url = new URL(window.location.href);
  url.searchParams.set('section', 'progress');
  url.searchParams.set('nutrition_period', period);
  if (period === 'custom') {
    url.searchParams.set('nutrition_from', dateFrom);
    url.searchParams.set('nutrition_to', dateTo);
  } else {
    url.searchParams.delete('nutrition_from');
    url.searchParams.delete('nutrition_to');
  }
  window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
}

function formatNumber(value: number | null | undefined, digits = 1): string {
  return value == null
    ? '—'
    : new Intl.NumberFormat('ru-RU', { maximumFractionDigits: digits }).format(value);
}

function formatDate(value: string, withYear = false): string {
  return formatCalendarDate(value, {
    day: 'numeric',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
  });
}

function periodLabel(report: NutritionReport): string {
  return `${formatDate(report.period_start, true)} — ${formatDate(report.period_end, true)}`;
}

function diaryLink(date: string): string {
  const returnTo = `${window.location.pathname}${window.location.search}#nutrition-period-report`;
  const params = new URLSearchParams({
    section: 'nutrition',
    date,
    return_to: returnTo,
  });
  return `/app?${params}`;
}

function weekMeta(
  point: DailyPoint | undefined,
  dayLink: ((date: string) => string) | null,
): WeekStripDayMeta {
  if (!point) {
    return { status: { key: 'upcoming', label: 'Вне выбранного периода' } };
  }
  const targetChange = point.target_changed ? ', цель изменилась' : '';
  const status = {
    complete: { key: 'completed' as const, label: `Заполнен${targetChange}` },
    incomplete: {
      key: 'in-progress' as const,
      pictogram: 'nutrition-incomplete' as const,
      label: `Не завершён${targetChange}`,
    },
    fasted: {
      key: 'completed' as const,
      pictogram: 'fasted' as const,
      label: `Отмечен день без приёмов пищи${targetChange}`,
    },
    missing: {
      key: 'neutral' as const,
      pictogram: 'missing' as const,
      label: `Нет данных${targetChange}`,
    },
  }[point.status];
  return {
    status,
    ...(dayLink
      ? { link: { label: 'Открыть дневник за этот день', to: dayLink(point.diary_date) } }
      : {}),
  };
}

function CoverageSummary({ report }: { report: NutritionReport }) {
  const { summary } = report;
  return (
    <div className="nutrition-report-coverage">
      <div>
        <span>Полнота дневника</span>
        <strong>
          Заполнено {summary.logged_days} из {summary.eligible_days} дней
        </strong>
        <p>Средние значения рассчитаны только по заполненным дням.</p>
      </div>
      <div
        aria-label={`Заполнено ${formatNumber(summary.coverage_percent)}% периода`}
        aria-valuemax={100}
        aria-valuemin={0}
        aria-valuenow={summary.coverage_percent}
        className="nutrition-report-coverage__meter"
        role="progressbar"
      >
        <span style={{ width: `${summary.coverage_percent}%` }} />
      </div>
      <p className="nutrition-report-coverage__details">
        {summary.incomplete_days} не завершено · {summary.missing_days} без данных ·{' '}
        {summary.fasted_days} отмечено без приёмов пищи
      </p>
    </div>
  );
}

function MetricRow({
  comparison,
  label,
  metric,
  unit,
}: {
  comparison: TargetComparison;
  label: string;
  metric: MetricSummary;
  unit: string;
}) {
  const deviation = comparison.average_deviation;
  return (
    <div className="nutrition-report-metric">
      <dt>{label}</dt>
      <dd>
        <strong>
          {formatNumber(metric.average, 0)} <span>{unit}</span>
        </strong>
        <small>
          {metric.sample_days
            ? `минимум ${formatNumber(metric.minimum, 0)} · максимум ${formatNumber(metric.maximum, 0)} · по ${metric.sample_days} дн.`
            : 'Нет данных по показателю'}
        </small>
      </dd>
      <dd>
        <span>Ориентир в среднем</span>
        <strong>
          {formatNumber(comparison.average_target, 0)}{' '}
          {comparison.average_target == null ? '' : <span>{unit}</span>}
        </strong>
        <small>
          {comparison.evaluated_days
            ? `сравнено ${comparison.evaluated_days} дн.`
            : 'Нет сопоставимых дней'}
        </small>
      </dd>
      <dd>
        <span>Отклонение</span>
        <strong>
          {deviation != null && deviation > 0 ? '+' : ''}
          {formatNumber(deviation, 0)} {deviation == null ? '' : <span>{unit}</span>}
        </strong>
      </dd>
    </div>
  );
}

function ReportMetrics({ report }: { report: NutritionReport }) {
  const { summary } = report;
  return (
    <dl className="nutrition-report-metrics" aria-label="Средние КБЖУ и ориентиры">
      <MetricRow
        label="Калории"
        metric={summary.calories}
        comparison={summary.calorie_comparison}
        unit="ккал"
      />
      <MetricRow
        label="Белок"
        metric={summary.protein_g}
        comparison={summary.protein_comparison}
        unit="г"
      />
      <MetricRow label="Жиры" metric={summary.fat_g} comparison={summary.fat_comparison} unit="г" />
      <MetricRow
        label="Углеводы"
        metric={summary.carbs_g}
        comparison={summary.carbs_comparison}
        unit="г"
      />
    </dl>
  );
}

function NutritionChart({
  dayLink,
  report,
}: {
  dayLink: ((date: string) => string) | null;
  report: NutritionReport;
}) {
  const [selectedIndex, setSelectedIndex] = useState(report.daily.length - 1);
  const width = 720;
  const height = 220;
  const insetX = 24;
  const insetY = 22;
  const values = report.daily.flatMap((point) =>
    [point.calories, point.target_calories].filter((value): value is number => value != null),
  );
  const maximum = Math.max(...values, 1) * 1.08;
  const x = (index: number) =>
    report.daily.length === 1
      ? width / 2
      : insetX + (index / (report.daily.length - 1)) * (width - insetX * 2);
  const y = (value: number) => height - insetY - (value / maximum) * (height - insetY * 2);
  const denseRange = report.daily.length > 7;
  const activeIndex = Math.min(selectedIndex, report.daily.length - 1);
  const activePoint = report.daily[activeIndex];
  const pointHitRadius = report.daily.length <= 7 ? 52 : 18;
  const hasActualValue = (
    point: NutritionReport['daily'][number] | undefined,
  ): point is NutritionReport['daily'][number] & { calories: number } =>
    Boolean(point && ['complete', 'fasted'].includes(point.status) && point.calories != null);
  const actualSegments = report.daily.slice(1).flatMap((point, index) => {
    const previous = report.daily[index];
    if (!hasActualValue(previous) || !hasActualValue(point)) {
      return [];
    }
    return [
      <line
        className="nutrition-report-chart__actual"
        key={`actual-${point.diary_date}`}
        x1={x(index)}
        x2={x(index + 1)}
        y1={y(previous.calories)}
        y2={y(point.calories)}
      />,
    ];
  });
  const targetSegments = report.daily.slice(1).flatMap((point, index) => {
    const previous = report.daily[index];
    if (!previous || previous.target_calories == null || point.target_calories == null) return [];
    return [
      <line
        className="nutrition-report-chart__target"
        key={`target-${point.diary_date}`}
        x1={x(index)}
        x2={x(index + 1)}
        y1={y(previous.target_calories)}
        y2={y(point.target_calories)}
      />,
    ];
  });
  const accessibleLabel = `Калории по дням за период ${periodLabel(report)}. Фактические значения: ${
    report.daily
      .filter((point) => point.calories != null)
      .map((point) => `${formatDate(point.diary_date)} — ${formatNumber(point.calories, 0)} ккал`)
      .join(', ') || 'нет заполненных дней'
  }.`;

  return (
    <figure className="nutrition-report-chart">
      <div className="nutrition-report-chart__legend" aria-hidden="true">
        <span>
          <i className="nutrition-report-chart__actual" /> Фактические калории
        </span>
        <span>
          <i className="nutrition-report-chart__target" /> Ориентир дня
        </span>
        <span>
          <i className="nutrition-report-chart__change" /> Смена цели
        </span>
      </div>
      <svg
        aria-label={accessibleLabel}
        preserveAspectRatio="none"
        role="img"
        viewBox={`0 0 ${width} ${height}`}
      >
        <line
          className="nutrition-report-chart__axis"
          x1={insetX}
          x2={width - insetX}
          y1={height - insetY}
          y2={height - insetY}
        />
        {targetSegments}
        {actualSegments}
        {report.daily.map((point, index) =>
          point.target_changed ? (
            <line
              className="nutrition-report-chart__change"
              key={`change-${point.diary_date}`}
              x1={x(index)}
              x2={x(index)}
              y1={insetY}
              y2={height - insetY}
            />
          ) : null,
        )}
        {denseRange && activePoint && (
          <line
            className="nutrition-report-chart__cursor"
            x1={x(activeIndex)}
            x2={x(activeIndex)}
            y1={insetY}
            y2={height - insetY}
          />
        )}
        {report.daily.map((point, index) =>
          ['complete', 'fasted'].includes(point.status) && point.calories != null ? (
            denseRange || !dayLink ? (
              <circle
                className="nutrition-report-chart__point"
                cx={x(index)}
                cy={y(point.calories)}
                key={point.diary_date}
                r="3.25"
              />
            ) : (
              <a
                aria-label={`${formatDate(point.diary_date, true)}: ${formatNumber(point.calories, 0)} ккал. Открыть дневник.`}
                href={dayLink(point.diary_date)}
                key={point.diary_date}
              >
                <circle
                  className="nutrition-report-chart__hit"
                  cx={x(index)}
                  cy={y(point.calories)}
                  r={pointHitRadius}
                />
                <circle
                  className="nutrition-report-chart__point"
                  cx={x(index)}
                  cy={y(point.calories)}
                  r="3.25"
                />
              </a>
            )
          ) : null,
        )}
      </svg>
      {denseRange && activePoint && (
        <div className="nutrition-report-chart__day-picker">
          <label>
            <span>День на графике</span>
            <input
              aria-label="Выбранный день графика"
              max={report.daily.length - 1}
              min={0}
              onChange={(event) => setSelectedIndex(Number(event.target.value))}
              type="range"
              value={activeIndex}
            />
          </label>
          <output>
            <strong>{formatDate(activePoint.diary_date, true)}</strong>
            <span>
              {statusLabels[activePoint.status]} ·{' '}
              {activePoint.calories == null
                ? 'калории —'
                : `${formatNumber(activePoint.calories, 0)} ккал`}
            </span>
          </output>
          {dayLink && (
            <AppLink
              aria-label={`Открыть дневник за ${formatDate(activePoint.diary_date, true)}`}
              to={dayLink(activePoint.diary_date)}
            >
              Открыть дневник
            </AppLink>
          )}
        </div>
      )}
      <figcaption>
        Калории, ккал · {periodLabel(report)}. Точки — фактические значения в подтверждённые дни;
        точка у нижней оси — 0 ккал. Линия соединяет только соседние подтверждённые дни.
      </figcaption>
    </figure>
  );
}

function TargetChanges({ report }: { report: NutritionReport }) {
  if (!report.target_changes.length) return null;
  return (
    <div className="nutrition-report-targets">
      <h3>Изменения цели в периоде</h3>
      <ol>
        {report.target_changes.map((target) => (
          <li key={`${target.effective_from}-${target.source}`}>
            <time dateTime={target.effective_from}>{formatDate(target.effective_from, true)}</time>
            <strong>{targetSourceLabels[target.source]}</strong>
            <span>
              {target.calories} ккал · Б {target.protein_g} · Ж {target.fat_g} · У {target.carbs_g}{' '}
              г
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function DailyTable({
  dayLink,
  report,
}: {
  dayLink: ((date: string) => string) | null;
  report: NutritionReport;
}) {
  return (
    <details
      className="nutrition-report-days"
      open={report.daily.length <= 30 && report.summary.logged_days > 0}
    >
      <summary>Дни периода: {report.daily.length}</summary>
      <div className="nutrition-report-days__table-wrap">
        <table>
          <caption className="sr-only">
            Дневные КБЖУ, статус заполнения и действовавшая цель
          </caption>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Статус</th>
              <th>Калории</th>
              <th>Б / Ж / У</th>
              <th>Цель</th>
              {dayLink && (
                <th>
                  <span className="sr-only">Действие</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {[...report.daily].reverse().map((point) => (
              <tr key={point.diary_date}>
                <td data-label="Дата">
                  <time dateTime={point.diary_date}>
                    {formatDate(point.diary_date, true)}
                    {point.is_current_day ? ' · сегодня' : ''}
                  </time>
                  {point.target_changed && <Badge>Новая цель</Badge>}
                </td>
                <td data-label="Статус">{statusLabels[point.status]}</td>
                <td data-label="Калории">
                  {point.calories == null ? '—' : `${formatNumber(point.calories, 0)} ккал`}
                </td>
                <td data-label="Б / Ж / У">
                  {point.protein_g == null
                    ? '—'
                    : `${formatNumber(point.protein_g, 0)} / ${formatNumber(point.fat_g, 0)} / ${formatNumber(point.carbs_g, 0)} г`}
                </td>
                <td data-label="Цель">
                  {point.target_calories == null ? 'Не задана' : `${point.target_calories} ккал`}
                </td>
                {dayLink && (
                  <td>
                    <AppLink
                      aria-label={`Открыть дневник за ${formatDate(point.diary_date, true)}`}
                      to={dayLink(point.diary_date)}
                    >
                      Открыть
                    </AppLink>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

export function NutritionPeriodReport({ clientId }: { clientId?: number }) {
  const initial = useMemo(
    () =>
      clientId == null
        ? initialReportState()
        : { period: 'days_30' as const, dateFrom: '', dateTo: '' },
    [clientId],
  );
  const [period, setPeriod] = useState<NutritionReportPeriod>(initial.period);
  const [selectedPeriod, setSelectedPeriod] = useState<NutritionReportPeriod>(initial.period);
  const [dateFrom, setDateFrom] = useState(initial.dateFrom);
  const [dateTo, setDateTo] = useState(initial.dateTo);
  const [customError, setCustomError] = useState('');
  const [exportState, setExportState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const dayLink = clientId == null ? diaryLink : null;
  const report = useQuery({
    queryKey: queryKeys.progress.nutritionReport(clientId ?? 'me', period, dateFrom, dateTo),
    queryFn: () => api<NutritionReport>(reportPath(period, dateFrom, dateTo, false, clientId)),
    placeholderData: keepPreviousData,
  });
  const today = report.data
    ? dateInputValue(new Date(), report.data.timezone)
    : dateInputValue(new Date());

  function selectPeriod(value: string): void {
    const next = value as NutritionReportPeriod;
    setSelectedPeriod(next);
    setCustomError('');
    if (next === 'custom') {
      setDateFrom((current) => current || report.data?.period_start || today);
      setDateTo((current) => current || report.data?.period_end || today);
      return;
    }
    setPeriod(next);
    setDateFrom('');
    setDateTo('');
    if (clientId == null) syncReportUrl(next, '', '');
  }

  function applyCustomPeriod(): void {
    if (!dateFrom || !dateTo) {
      setCustomError('Укажите дату начала и окончания.');
      return;
    }
    const days =
      Math.floor(
        (Date.parse(`${dateTo}T00:00:00Z`) - Date.parse(`${dateFrom}T00:00:00Z`)) / 86_400_000,
      ) + 1;
    if (days < 1) {
      setCustomError('Дата окончания не может быть раньше даты начала.');
      return;
    }
    if (days > 366) {
      setCustomError('Период не может превышать 366 дней.');
      return;
    }
    if (dateTo > today) {
      setCustomError('Отчёт нельзя построить за будущие даты.');
      return;
    }
    setCustomError('');
    setPeriod('custom');
    if (clientId == null) syncReportUrl('custom', dateFrom, dateTo);
  }

  async function downloadCsv(): Promise<void> {
    setExportState('loading');
    try {
      const file = await apiFile(reportPath(period, dateFrom, dateTo, true, clientId));
      const url = URL.createObjectURL(file.blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.filename ?? 'nutrition-report.csv';
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setExportState('done');
    } catch {
      setExportState('error');
    }
  }

  const pointsByDate = new Map(report.data?.daily.map((point) => [point.diary_date, point]));
  const showWeek = report.data && ['days_7', 'current_week'].includes(report.data.period);

  return (
    <section
      className="progress-section nutrition-period-report"
      id="nutrition-period-report"
      aria-labelledby="nutrition-period-report-title"
    >
      <header className="progress-section__head nutrition-period-report__head">
        <div>
          <span className="progress-section__eyebrow">Фактический дневник</span>
          <h2 id="nutrition-period-report-title">Отчёт по питанию</h2>
          <p>Полнота данных, КБЖУ и цели, которые действовали в каждый день периода.</p>
        </div>
        <Button
          disabled={!report.data || exportState === 'loading'}
          onClick={() => void downloadCsv()}
          type="button"
          variant="secondary"
        >
          {exportState === 'loading' ? 'Готовим CSV…' : 'Скачать CSV'}
        </Button>
      </header>

      <div className="nutrition-period-report__selector">
        <SegmentedControl
          ariaLabel="Период отчёта по питанию"
          value={selectedPeriod}
          options={reportPeriods}
          onChange={selectPeriod}
        />
      </div>
      <p className="nutrition-period-report__selector-hint" aria-hidden="true">
        Ещё периоды — свайпните влево
      </p>
      {selectedPeriod === 'custom' && (
        <div
          className="nutrition-period-report__custom"
          aria-describedby={customError ? 'nutrition-report-custom-error' : undefined}
        >
          <Field label="Начало периода" labelFor="nutrition-report-from">
            <DateInput
              id="nutrition-report-from"
              max={dateTo || today}
              onChange={(event) => setDateFrom(event.target.value)}
              value={dateFrom}
            />
          </Field>
          <Field label="Конец периода" labelFor="nutrition-report-to">
            <DateInput
              id="nutrition-report-to"
              max={today}
              min={dateFrom}
              onChange={(event) => setDateTo(event.target.value)}
              value={dateTo}
            />
          </Field>
          <Button onClick={applyCustomPeriod} type="button" variant="secondary">
            Показать период
          </Button>
          {customError && (
            <p className="ui-field__error" id="nutrition-report-custom-error" role="alert">
              {customError}
            </p>
          )}
        </div>
      )}

      {report.isLoading && !report.data ? (
        <LoadingState label="Собираем отчёт по питанию…" />
      ) : report.error && !report.data ? (
        <ErrorState message={(report.error as Error).message} retry={() => void report.refetch()} />
      ) : report.data ? (
        <>
          <div className="nutrition-period-report__period">
            <strong>{periodLabel(report.data)}</strong>
            <span>Часовой пояс: {report.data.timezone}</span>
            {report.isFetching && <span role="status">Обновляем данные…</span>}
          </div>
          {report.error && (
            <ErrorState
              message={(report.error as Error).message}
              retry={() => void report.refetch()}
            />
          )}
          <CoverageSummary report={report.data} />
          {showWeek && (
            <WeekStrip
              anchorDate={report.data.period_start}
              ariaLabel="Дни отчёта по питанию"
              getDayMeta={(date) => weekMeta(pointsByDate.get(date), dayLink)}
              legend={NUTRITION_WEEK_LEGEND}
              mode="overview"
              rangeStart={report.data.period_start}
              title="Дни отчёта"
              today={report.data.daily.find((point) => point.is_current_day)?.diary_date ?? ''}
            />
          )}
          {report.data.summary.logged_days === 0 ? (
            <div className="nutrition-period-report__empty">
              <EmptyState
                title="Нет заполненных дней за период"
                text="Неполные дни и отсутствие записей не превращаются в нулевые значения."
              />
              {clientId == null && (
                <AppLink className="button-link" to="/app?section=nutrition">
                  Открыть дневник питания
                </AppLink>
              )}
            </div>
          ) : (
            <>
              <ReportMetrics report={report.data} />
              <div className="nutrition-report-adherence" aria-label="Сравнение с целью">
                <p>
                  <strong>
                    {report.data.summary.days_within_calorie_tolerance} из{' '}
                    {report.data.summary.calorie_tolerance_evaluated_days}
                  </strong>
                  <span>дней в пределах ±10% ориентира калорий</span>
                </p>
                <p>
                  <strong>
                    {report.data.summary.days_meeting_protein_target} из{' '}
                    {report.data.summary.protein_target_evaluated_days}
                  </strong>
                  <span>дней с достигнутым ориентиром белка</span>
                </p>
              </div>
              <NutritionChart
                dayLink={dayLink}
                key={`${report.data.period_start}-${report.data.period_end}`}
                report={report.data}
              />
            </>
          )}
          <TargetChanges report={report.data} />
          <DailyTable dayLink={dayLink} report={report.data} />
          <p className="progress-note nutrition-period-report__methodology">
            Отчёт описывает только записи КБЖУ. Он не оценивает качество рациона, витамины, здоровье
            или причины изменения веса. Неполные дни видны в списке, но не входят в средние и
            сравнение с целью.
          </p>
        </>
      ) : null}
      <span aria-live="polite" className="sr-only">
        {exportState === 'done'
          ? 'CSV отчёт скачан.'
          : exportState === 'error'
            ? 'Не удалось скачать CSV отчёт.'
            : ''}
      </span>
    </section>
  );
}
