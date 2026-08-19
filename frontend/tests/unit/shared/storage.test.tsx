import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { usePersistentState } from '../../../src/shared/storage';
import { clearSensitiveUserScopedStorage } from '../../../src/shared/userScopedStorage';

function Harness({ storageKey, initial }: { storageKey: string; initial: string }) {
  const [value, setValue] = usePersistentState(storageKey, initial);
  return (
    <label>
      Черновик
      <input
        aria-label="Черновик"
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
    </label>
  );
}

describe('usePersistentState account scope', () => {
  beforeEach(() => localStorage.clear());
  afterEach(cleanup);

  it('does not copy the previous account value when its storage key changes', async () => {
    const view = render(<Harness storageKey="fit_profile_draft_7" initial="Профиль 7" />);
    const input = screen.getByRole('textbox', { name: 'Черновик' });
    await userEvent.clear(input);
    await userEvent.type(input, 'Секрет аккаунта 7');
    await waitFor(() =>
      expect(localStorage.getItem('fit_profile_draft_7')).toBe('"Секрет аккаунта 7"'),
    );

    clearSensitiveUserScopedStorage();
    view.rerender(<Harness storageKey="fit_profile_draft_8" initial="Профиль 8" />);

    await waitFor(() => expect(input).toHaveValue('Профиль 8'));
    expect(localStorage.getItem('fit_profile_draft_7')).toBeNull();
    expect(localStorage.getItem('fit_profile_draft_8')).not.toContain('Секрет аккаунта 7');
  });
});
