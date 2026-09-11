import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Mocked } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import { App } from './App';

vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

describe('App Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock implementation for axios.interceptors.response.use
    (mockedAxios.interceptors.response.use as unknown as ReturnType<typeof vi.fn>).mockImplementation(() => 0);
  });

  it('completes setup and transitions to login without looping', async () => {
    // 1. Initial load says setup IS required
    mockedAxios.get.mockResolvedValueOnce({ data: { setup_required: true } });
    // 2. Setup POST succeeds
    mockedAxios.post.mockResolvedValueOnce({});

    render(<App />);

    // Should show Setup screen
    expect(await screen.findByRole('heading', { name: /Первоначальная настройка/i })).toBeInTheDocument();

    const user = userEvent.setup();
    const passwordInput = screen.getByLabelText(/Пароль/i);
    await user.type(passwordInput, 'secretpassword');

    const submitBtn = screen.getByRole('button', { name: /Создать аккаунт/i });
    await user.click(submitBtn);

    // Verify API was called
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/setup', {
      username: 'admin',
      password: 'secretpassword',
    });

    // We should now see the Login screen, NOT loop back to Setup
    expect(await screen.findByRole('heading', { name: /Вход в систему/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /Первоначальная настройка/i })).not.toBeInTheDocument();
  });
});
