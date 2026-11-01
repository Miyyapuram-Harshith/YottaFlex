/**
 * Canonical Formatters Module
 * Guarantees standard en-US currency formatting ($1,234,567.89),
 * tabular number formatting, ISO-8601 UTC date formatting,
 * and exact Hamilton-Hare largest-remainder rounding (sums to 100.0%).
 */

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const intFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 0,
});

/**
 * Formats a monetary amount into strict $X,XXX.XX format (en-US).
 * Never uses Indian digit grouping; always exactly 2 decimal places.
 */
export function formatCurrency(value: number | string | null | undefined, isCents = false): string {
  if (value === null || value === undefined || value === '') {
    return '$0.00';
  }
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) {
    return '$0.00';
  }
  const dollars = isCents ? num / 100 : num;
  return currencyFormatter.format(dollars);
}

/**
 * Formats integer counts with commas (e.g. 30,000).
 */
export function formatInt(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '0';
  }
  const num = typeof value === 'string' ? parseInt(value, 10) : value;
  if (isNaN(num)) {
    return '0';
  }
  return intFormatter.format(num);
}

/**
 * Formats percentages with fixed decimals (e.g. 85.2%).
 */
export function formatPercent(value: number | string | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || value === '') {
    return '0.0%';
  }
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) {
    return '0.0%';
  }
  return `${num.toFixed(decimals)}%`;
}

/**
 * Formats ISO-8601 timestamps to readable UTC strings.
 */
export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) {
    return '—';
  }
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) {
      return isoString;
    }
    const year = d.getUTCFullYear();
    const month = String(d.getUTCMonth() + 1).padStart(2, '0');
    const day = String(d.getUTCDate()).padStart(2, '0');
    const hours = String(d.getUTCHours()).padStart(2, '0');
    const mins = String(d.getUTCMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${mins} UTC`;
  } catch {
    return isoString;
  }
}

/**
 * Largest-Remainder Method (Hamilton-Hare)
 * Computes percentage distribution that sums to EXACTLY 100.0%.
 */
export function calculateLargestRemainder(counts: number[], decimals = 1): number[] {
  const sum = counts.reduce((a, b) => a + b, 0);
  if (sum === 0) {
    return counts.map(() => 0);
  }
  const factor = Math.pow(10, decimals);
  const targetTotal = 100 * factor;

  const rawPercentages = counts.map(c => (c / sum) * 100);
  const floors = rawPercentages.map(p => Math.floor(p * factor));
  const floorSum = floors.reduce((a, b) => a + b, 0);
  const remainder = targetTotal - floorSum;

  const remainders = rawPercentages.map((p, i) => ({
    index: i,
    rem: (p * factor) - floors[i],
  }));

  // Sort descending by fractional remainder
  remainders.sort((a, b) => b.rem - a.rem);

  const result = [...floors];
  for (let i = 0; i < remainder; i++) {
    result[remainders[i].index] += 1;
  }

  return result.map(v => v / factor);
}
