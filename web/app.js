const $ = (id) => document.getElementById(id);
const scenarioSelect = $('scenario-select');
const disruptionSelect = $('disruption-select');
let data;

const scenarioLabels = {
  ordinary: 'Ordinary week',
  event_low: 'Event week · Low',
  event_medium: 'Event week · Medium',
  event_high: 'Event week · High',
};
const disruptionLabels = {
  none: 'No disruption',
  two_callouts: 'Two staff call-outs',
  four_arrival_surge: 'Four extra arrivals · Day 4, 3 PM',
};

function setDisruptionOptions() {
  const isMedium = scenarioSelect.value === 'event_medium';
  disruptionSelect.innerHTML = '<option value="none">No disruption</option>';
  if (isMedium) {
    disruptionSelect.insertAdjacentHTML('beforeend', '<option value="two_callouts">Two staff call-outs</option><option value="four_arrival_surge">Four extra arrivals · Day 4, 3 PM</option>');
  }
  disruptionSelect.disabled = !isMedium;
  $('scenario-note-text').textContent = {
    ordinary: 'Ordinary week demand. No event increase applied.',
    event_low: 'Low assumes 15% more arrivals than an ordinary week.',
    event_medium: 'Medium assumes 40% more arrivals than an ordinary week.',
    event_high: 'High assumes 70% more arrivals than an ordinary week.',
  }[scenarioSelect.value];
}

function currentMetrics(plan) {
  return data.metrics.find((row) => row.scenario === scenarioSelect.value && row.disruption === disruptionSelect.value && row.plan === plan);
}

function displaySchedule() {
  const baseline = currentMetrics('baseline');
  const recommended = currentMetrics('recommended');
  if (!baseline || !recommended) return;

  const baseCoverage = Number(baseline.coverage_percent);
  const recCoverage = Number(recommended.coverage_percent);
  $('task-hours').textContent = `${Number(recommended.task_hours).toFixed(1)}h`;
  $('baseline-coverage').textContent = `${baseCoverage.toFixed(1)}%`;
  $('recommended-coverage').textContent = `${recCoverage.toFixed(1)}%`;
  $('baseline-uncovered').textContent = `${Number(baseline.uncovered_task_hours).toFixed(1)}h uncovered`;
  $('recommended-uncovered').textContent = `${Number(recommended.uncovered_task_hours).toFixed(1)}h uncovered`;
  $('scheduled-hours').textContent = `${recommended.scheduled_worker_hours}h`;
  $('hours-change').textContent = `${baseline.scheduled_worker_hours}h baseline · same worker pool`;
  $('baseline-bar').style.width = `${baseCoverage}%`;
  $('recommended-bar').style.width = `${recCoverage}%`;
  $('baseline-bar-label').textContent = `${baseCoverage.toFixed(1)}%`;
  $('recommended-bar-label').textContent = `${recCoverage.toFixed(1)}%`;
  $('case-label').textContent = `${scenarioLabels[scenarioSelect.value]} · ${disruptionLabels[disruptionSelect.value]}`;

  const delta = Number(baseline.uncovered_task_hours) - Number(recommended.uncovered_task_hours);
  if (delta > 0) {
    $('insight-title').textContent = `${delta.toFixed(1)} fewer uncovered hours`;
    $('insight-text').textContent = `The recommended shift placement covers more estimated work with the same scheduled worker-hours. This result is from the synthetic demo scenario.`;
  } else if (delta < 0) {
    $('insight-title').textContent = `${Math.abs(delta).toFixed(1)} more uncovered hours`;
    $('insight-text').textContent = `The recommended plan does not cover this scenario as well as the baseline. The manager can review the gap and adjust assumptions or staffing.`;
  } else {
    $('insight-title').textContent = 'Same coverage';
    $('insight-text').textContent = 'Both schedules cover the same estimated work in this scenario.';
  }

  renderRoster();
  $('approval-status').textContent = 'Awaiting manager review';
  $('approval-status').className = 'approval-status';
  $('approve-button').disabled = false;
  $('reject-button').disabled = false;
}

function renderRoster() {
  const roles = Object.fromEntries(data.workers.map((worker) => [worker.worker_id, worker.role]));
  const shifts = data.shifts.filter((row) => row.scenario === scenarioSelect.value && row.disruption === disruptionSelect.value && row.plan === 'recommended');
  const grouped = new Map();
  for (const shift of shifts) {
    const key = `${shift.day}|${shift.start_hour}|${shift.end_hour}|${roles[shift.worker_id] || 'other'}`;
    if (!grouped.has(key)) grouped.set(key, {day: Number(shift.day), start: Number(shift.start_hour), end: Number(shift.end_hour), role: roles[shift.worker_id] || 'other', ids: []});
    grouped.get(key).ids.push(shift.worker_id);
  }
  const rows = [...grouped.values()].sort((a,b) => a.day-b.day || a.start-b.start || a.role.localeCompare(b.role));
  $('roster-count').textContent = `${shifts.length} worker shifts`;
  $('roster-body').innerHTML = rows.length ? rows.map((r) => `<tr><td>Day ${r.day}</td><td>${formatHour(r.start)}–${formatHour(r.end)}</td><td><span class="role-pill">${escapeText(r.role.replaceAll('_',' '))}</span></td><td>${r.ids.length}</td><td class="team-ids">${r.ids.map(escapeText).join(', ')}</td></tr>`).join('') : '<tr><td colspan="5">No shifts for this scenario.</td></tr>';
}

function formatHour(hour) {
  const h = hour % 24;
  const suffix = h >= 12 ? 'PM' : 'AM';
  const display = h % 12 || 12;
  return `${display} ${suffix}`;
}
function escapeText(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

async function recordDecision(decision) {
  const response = await fetch('/api/approval', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({scenario: scenarioSelect.value, disruption: disruptionSelect.value, decision}),
  });
  if (!response.ok) throw new Error('Could not save manager decision.');
  const result = await response.json();
  $('approval-status').textContent = `${decision === 'approved' ? 'Approved' : 'Rejected'} · saved ${result.timestamp}`;
  $('approval-status').className = `approval-status ${decision}`;
  $('approve-button').disabled = true;
  $('reject-button').disabled = true;
}

scenarioSelect.addEventListener('change', () => { setDisruptionOptions(); displaySchedule(); });
disruptionSelect.addEventListener('change', displaySchedule);
$('approve-button').addEventListener('click', () => recordDecision('approved').catch(showError));
$('reject-button').addEventListener('click', () => recordDecision('rejected').catch(showError));
function showError(error) { $('approval-status').textContent = error.message; }

fetch('/api/data').then((response) => {
  if (!response.ok) throw new Error('Could not load demo data.');
  return response.json();
}).then((result) => {
  data = result;
  setDisruptionOptions();
  displaySchedule();
}).catch((error) => {
  $('insight-title').textContent = 'Demo data not ready';
  $('insight-text').textContent = `${error.message} Run the data generation and planner commands, then reload this page.`;
});
