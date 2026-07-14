async function loadEvents() {
  const response = await fetch('/events');
  const payload = await response.json();
  const events = payload.events || [];
  const timeline = document.getElementById('timeline');
  timeline.innerHTML = '';

  let blocked = 0;
  let secrets = 0;
  let saved = 0;

  for (const event of events) {
    if (event.kind.includes('blocked') || event.kind.includes('error')) blocked += 1;
    if (event.kind === 'secret_redacted') secrets += 1;
    if (event.data && event.data.cost && event.data.cost.cache_savings) saved += event.data.cost.cache_savings;

    const row = document.createElement('article');
    row.className = `event ${event.kind}`;
    const time = new Date(event.ts * 1000).toLocaleTimeString();
    row.innerHTML = `
      <div class="time">${time}<br>${event.kind}</div>
      <div class="agent">${event.agent}</div>
      <div>
        <div class="summary"></div>
        <pre></pre>
      </div>
    `;
    row.querySelector('.summary').textContent = event.summary;
    row.querySelector('pre').textContent = JSON.stringify(event.data || {}, null, 2);
    timeline.appendChild(row);
  }

  document.getElementById('eventsCount').textContent = events.length;
  document.getElementById('blockedCount').textContent = blocked;
  document.getElementById('secretCount').textContent = secrets;
  document.getElementById('savedCost').textContent = `$${saved.toFixed(4)}`;
}

loadEvents();
setInterval(loadEvents, 1500);

