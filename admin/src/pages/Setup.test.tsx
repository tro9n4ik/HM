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
    expect(screen.getByText('Home.Media Setup')).toBeDefined();
    expect(screen.getByText('Admin Username')).toBeDefined();
    expect(screen.getByText('Password')).toBeDefined();
  });
});
