import { describe, it, expect } from 'vitest';
import { formatCurrency, formatInt, formatPercent, formatDate, calculateLargestRemainder } from './formatters';

describe('formatCurrency', () => {
  it('formats zero correctly', () => {
    expect(formatCurrency(0)).toBe('$0.00');
    expect(formatCurrency('0')).toBe('$0.00');
  });

  it('formats negative numbers correctly', () => {
    expect(formatCurrency(-123.45)).toBe('-$123.45');
    expect(formatCurrency(-5000, true)).toBe('-$50.00');
  });

  it('formats floating point values without dropping trailing zeroes (en-US)', () => {
    expect(formatCurrency(2400944.5)).toBe('$2,400,944.50');
    expect(formatCurrency(31354083.38)).toBe('$31,354,083.38');
    expect(formatCurrency(191645.25)).toBe('$191,645.25');
  });

  it('formats integer cents when isCents flag is true', () => {
    expect(formatCurrency(15604119, true)).toBe('$156,041.19');
    expect(formatCurrency(3560406, true)).toBe('$35,604.06');
  });
});

describe('formatInt', () => {
  it('formats integer counts with standard en-US grouping', () => {
    expect(formatInt(30000)).toBe('30,000');
    expect(formatInt(8000)).toBe('8,000');
    expect(formatInt(0)).toBe('0');
  });
});

describe('formatPercent', () => {
  it('formats percentages with given decimals', () => {
    expect(formatPercent(85.16, 1)).toBe('85.2%');
    expect(formatPercent(100.0, 1)).toBe('100.0%');
    expect(formatPercent(0, 1)).toBe('0.0%');
  });
});

describe('formatDate', () => {
  it('formats ISO-8601 timestamps to UTC', () => {
    expect(formatDate('2026-03-01T10:00:00Z')).toBe('2026-03-01 10:00 UTC');
  });
});

describe('calculateLargestRemainder', () => {
  it('guarantees percentages sum to exactly 100.0%', () => {
    // 8,734 / 616 / 1,585 / 398 = 11,333
    const counts = [8734, 616, 1585, 398];
    const percentages = calculateLargestRemainder(counts, 1);
    expect(percentages).toHaveLength(4);
    const sum = percentages.reduce((a, b) => a + b, 0);
    expect(sum).toBe(100.0);
    expect(percentages[0]).toBe(77.1);
    expect(percentages[1]).toBe(5.4);
    expect(percentages[2]).toBe(14.0);
    expect(percentages[3]).toBe(3.5);
  });
});
