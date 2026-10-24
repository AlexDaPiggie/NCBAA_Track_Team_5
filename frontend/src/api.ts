export async function apiError(response: Response, endpoint: string): Promise<Error> {
  const body = await response.text();
  if (response.status === 404) {
    return new Error(`The backend returned 404 for ${endpoint}. Start the Apron API from the project root. See the README troubleshooting steps.`);
  }

  try {
    const detail = JSON.parse(body).detail;
    if (typeof detail === 'string' && detail.length > 0) return new Error(detail);
  } catch {
    // Use the plain-text response below.
  }

  const message = body.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  return new Error(message || `Request failed (${response.status}) for ${endpoint}.`);
}
