import type { ComponentPropsWithoutRef } from 'react';

type PickerInputProps = Omit<ComponentPropsWithoutRef<'input'>, 'type'> & {
  controlClassName?: string;
};

export function DateInput({ controlClassName = '', ...props }: PickerInputProps) {
  return (
    <div className={`date-control ${controlClassName}`.trim()}>
      <input {...props} type="date" />
    </div>
  );
}

export function TimeInput({ controlClassName = '', ...props }: PickerInputProps) {
  return (
    <div className={`time-control ${controlClassName}`.trim()}>
      <input {...props} type="time" />
    </div>
  );
}
