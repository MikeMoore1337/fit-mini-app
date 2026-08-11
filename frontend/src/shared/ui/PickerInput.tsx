import type { ComponentPropsWithoutRef } from 'react';

type DateInputProps = Omit<ComponentPropsWithoutRef<'input'>, 'type'> & {
  controlClassName?: string;
};

export function DateInput({ controlClassName = '', ...props }: DateInputProps) {
  return (
    <div className={`date-control ${controlClassName}`.trim()}>
      <input {...props} type="date" />
    </div>
  );
}
