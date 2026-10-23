import React from 'react';

export default function WorkflowIntro(){
  return <section className="welcome-panel" aria-label="How the staffing planner works">
    <div className="welcome-copy">
      <span className="eyebrow">SUPER BOWL LXI · LOS ANGELES · 7-DAY PLAN</span>
      <h2>Plan staff for event week.</h2>
      <p>Compare an ordinary week with event demand. Build shifts. Test call-outs and arrival surges. Review the draft before approval.</p>
    </div>
    <div className="workflow-steps">
      <article><span>01</span><b>Choose demand</b><small>Set low, medium, or high. Pick a data source.</small></article>
      <article><span>02</span><b>Build shifts</b><small>Set work limits and create a seven-day roster.</small></article>
      <article><span>03</span><b>Test and review</b><small>Compare plans under the same disruption. A manager decides.</small></article>
    </div>
    <div className="welcome-note"><b>Planning demo</b><span>LA FBO demand is not available here. Results use synthetic data or a clearly labeled JFK proxy. No worker dispatch or aircraft movement control.</span></div>
  </section>;
}
