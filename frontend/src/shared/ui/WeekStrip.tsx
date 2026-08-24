import { useId, type ReactNode } from 'react';
import { addCalendarDays, calendarWeek, formatCalendarDate } from '../dateTime';
import { AppLink } from '../navigation/router';
import { ChevronIcon } from './common';

export type WeekStripStatusKey =
  'completed' | 'in-progress' | 'planned' | 'upcoming' | 'skipped' | 'neutral';

export interface WeekStripStatus {
  key: WeekStripStatusKey;
  label: string;
  marker?: string;
}

export interface WeekStripDayMeta {
  link?: {
    label: string;
    onClick?: () => void;
    to: string;
  };
  status?: WeekStripStatus | null;
}

interface WeekStripNavigation {
  nextDisabled?: boolean;
  onNext(): void;
  onPrevious(): void;
}

interface WeekStripCommonProps {
  anchorDate: string;
  ariaLabel: string;
  headerAction?: ReactNode;
  loading?: boolean;
  loadingLabel?: string;
  navigation?: WeekStripNavigation;
  title: string;
  today: string;
  /** Optional exact first day for rolling seven-day report contexts. */
  rangeStart?: string;
}

type WeekStripProps = WeekStripCommonProps &
  (
    | {
        getDayMeta?: (date: string) => WeekStripDayMeta;
        mode: 'overview';
        isDateDisabled?: never;
        onSelect?: never;
        selectedDate?: never;
      }
    | {
        getDayMeta?: never;
        isDateDisabled?: (date: string) => boolean;
        mode: 'picker';
        onSelect(date: string): void;
        selectedDate: string;
      }
  );

export function formatWeekRange(days: string[]): string {
  const first = days[0];
  const last = days.at(-1);
  if (!first || !last) return '';

  const sameMonth = first.slice(0, 7) === last.slice(0, 7);
  const sameYear = first.slice(0, 4) === last.slice(0, 4);
  const firstLabel = formatCalendarDate(first, {
    day: 'numeric',
    ...(sameMonth ? {} : { month: 'short' }),
    ...(sameYear ? {} : { year: 'numeric' }),
  });
  const lastLabel = formatCalendarDate(last, {
    day: 'numeric',
    month: 'short',
    ...(sameYear ? {} : { year: 'numeric' }),
  });
  return `${firstLabel} — ${lastLabel}`;
}

export function WeekStrip(props: WeekStripProps) {
  const headingId = useId();
  const days = props.rangeStart
    ? Array.from({ length: 7 }, (_, index) => addCalendarDays(props.rangeStart!, index))
    : calendarWeek(props.anchorDate);
  const isPicker = props.mode === 'picker';
  const Root = isPicker ? 'nav' : 'section';

  return (
    <Root
      aria-busy={props.loading || undefined}
      aria-label={isPicker ? props.ariaLabel : undefined}
      aria-labelledby={isPicker ? undefined : headingId}
      className={`week-strip week-strip--${props.mode}`}
    >
      <div
        className={`week-strip__head week-strip__head--${props.navigation ? 'navigation' : 'static'}`}
      >
        {props.navigation && (
          <button
            aria-label="Предыдущая неделя"
            className="week-strip__nav week-strip__nav--previous"
            onClick={props.navigation.onPrevious}
            type="button"
          >
            <ChevronIcon direction="left" />
            <span>Неделя</span>
          </button>
        )}

        <div className="week-strip__context">
          <h2 id={headingId}>{props.title}</h2>
          <span>{formatWeekRange(days)}</span>
        </div>

        {props.navigation ? (
          <button
            aria-label="Следующая неделя"
            className="week-strip__nav week-strip__nav--next"
            disabled={props.navigation.nextDisabled}
            onClick={props.navigation.onNext}
            type="button"
          >
            <span>Неделя</span>
            <ChevronIcon direction="right" />
          </button>
        ) : (
          props.headerAction && (
            <div className="week-strip__header-action">{props.headerAction}</div>
          )
        )}
      </div>

      <ol className="week-strip__days">
        {days.map((date) => {
          const isToday = date === props.today;
          const isSelected = isPicker && date === props.selectedDate;
          const dayMeta = props.mode === 'overview' ? props.getDayMeta?.(date) : undefined;
          const status = dayMeta?.status;
          const label = [
            formatCalendarDate(date, { weekday: 'long', day: 'numeric', month: 'long' }),
            isToday ? 'сегодня' : null,
            isSelected ? 'выбрано' : null,
            status?.label,
            dayMeta?.link?.label,
          ]
            .filter(Boolean)
            .join(', ');
          const content = (
            <>
              <span className="week-strip__weekday">
                {formatCalendarDate(date, { weekday: 'short' }).replace('.', '')}
              </span>
              <strong>{formatCalendarDate(date, { day: 'numeric' })}</strong>
              <span
                aria-hidden="true"
                className={`week-strip__marker${status ? ` week-strip__marker--${status.key}` : ''}`}
              >
                {status?.marker ?? ''}
              </span>
            </>
          );
          const dayClassName = `week-strip__day${dayMeta?.link ? ' week-strip__day--interactive' : ''}`;

          return (
            <li key={date}>
              {isPicker ? (
                <button
                  aria-current={isToday ? 'date' : undefined}
                  aria-label={label}
                  aria-pressed={isSelected}
                  className={dayClassName}
                  disabled={props.isDateDisabled?.(date)}
                  onClick={() => props.onSelect(date)}
                  type="button"
                >
                  {content}
                </button>
              ) : dayMeta?.link ? (
                <AppLink
                  aria-current={isToday ? 'date' : undefined}
                  aria-label={label}
                  className={dayClassName}
                  onClick={dayMeta.link.onClick}
                  to={dayMeta.link.to}
                >
                  {content}
                </AppLink>
              ) : (
                <div
                  aria-current={isToday ? 'date' : undefined}
                  aria-label={label}
                  className={dayClassName}
                  role="group"
                >
                  {content}
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {props.loading && (
        <span className="sr-only" role="status">
          {props.loadingLabel ?? 'Загружаем данные недели'}
        </span>
      )}
    </Root>
  );
}
