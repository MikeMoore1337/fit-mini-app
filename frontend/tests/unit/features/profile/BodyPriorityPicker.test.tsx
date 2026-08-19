import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import {
  BodyPriorityPicker,
  isBodyPriorityComplete,
} from '../../../../src/features/profile/BodyPriorityPicker';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));

describe('BodyPriorityPicker', () => {
  it('loads canonical options and requires at least one selected group', async () => {
    apiMock.mockResolvedValue({
      items: [
        { id: 'chest', name: 'Грудь' },
        { id: 'back', name: 'Спина' },
      ],
    });
    const onChange = vi.fn();
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <BodyPriorityPicker
          value={{ mode: 'muscle_groups', muscle_group_ids: [] }}
          onChange={onChange}
        />
      </QueryClientProvider>,
    );

    expect(await screen.findByLabelText('Грудь')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Выберите хотя бы одну');
    fireEvent.click(screen.getByLabelText('Грудь'));
    expect(onChange).toHaveBeenLastCalledWith({
      mode: 'muscle_groups',
      muscle_group_ids: ['chest'],
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <BodyPriorityPicker
          value={{ mode: 'muscle_groups', muscle_group_ids: ['chest'] }}
          onChange={onChange}
        />
      </QueryClientProvider>,
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(isBodyPriorityComplete({ mode: 'muscle_groups', muscle_group_ids: ['chest'] })).toBe(
      true,
    );
    expect(isBodyPriorityComplete({ mode: 'muscle_groups', muscle_group_ids: [] })).toBe(false);
    expect(isBodyPriorityComplete({ mode: 'balanced', muscle_group_ids: [] })).toBe(true);
  });
});
