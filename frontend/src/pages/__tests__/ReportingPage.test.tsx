import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import ReportingPage from '../ReportingPage';

describe('ReportingPage Component', () => {
  const renderReportingPage = () => {
    return render(
      <BrowserRouter>
        <ReportingPage />
      </BrowserRouter>
    );
  };

  test('renders v1 out-of-scope placeholder', () => {
    renderReportingPage();
    expect(screen.getByText('Out of Scope (v1)')).toBeInTheDocument();
  });
});
