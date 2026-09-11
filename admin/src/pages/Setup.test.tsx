import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Setup } from './Setup';

describe('Setup', () => {
  it('renders setup form', () => {
    render(
      <BrowserRouter>
        <Setup />
      </BrowserRouter>
    );
    expect(screen.getByText('Первоначальная настройка')).toBeDefined();
    expect(screen.getByText('Имя администратора')).toBeDefined();
    expect(screen.getByText('Пароль')).toBeDefined();
  });
});
