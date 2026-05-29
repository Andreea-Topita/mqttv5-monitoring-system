export function getApiErrorMessage(err: any, fallback: string): string {
  if (err?.error?.error?.message) {
    return err.error.error.message;
  }

  if (typeof err?.error?.detail === 'string') {
    return err.error.detail;
  }

  if (Array.isArray(err?.error?.detail)) {
    return err.error.detail
      .map((item: any) => item?.msg)
      .filter(Boolean)
      .join(' ');
  }

  return fallback;
}