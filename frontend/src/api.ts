export async function apiError(response: Response, endpoint: string): Promise<Error> {
  const body = await response.text();
  if (response.status === 404) {
    return new Error(`The planner returned 404 for ${endpoint}. Start the CrewPilot API from the project root. See the README troubleshooting steps.`);
  }

  try {
    const detail = JSON.parse(body).detail;
    if (typeof detail === 'string' && detail.length > 0) return new Error(detail);
    if (Array.isArray(detail) && detail.length) {
      return new Error(detail.slice(0, 3).map((issue: {loc?: (string|number)[]; msg?: string}) => {
        const field = (issue.loc ?? []).filter(part => part !== 'body' && part !== 'inputs').join(' → ').replaceAll('_', ' ');
        return `${field || 'Input'}: ${issue.msg || 'invalid value'}`;
      }).join('. '));
    }
  } catch {
    // Use the plain-text response below.
  }

  const message = body.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  return new Error(message || `Request failed (${response.status}) for ${endpoint}.`);
}
