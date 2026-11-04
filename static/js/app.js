/**
 * IBM Travel Planner Agent - Main JavaScript
 * Handles all UI interactions and API calls.
 */

const API_BASE = '/api';
let currentSessionId = 'session_' + Date.now();
let currentPanel = 'chat';

// ─── Utility ───────────────────────────────────────────────────────────────

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function today() {
  return new Date().toISOString().split('T')[0];
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = String(text || '');
  return div.innerHTML;
}

function showLoading(id, msg = 'Fetching results from IBM Granite…') {
  const el = document.getElementById(id);
  if (el) { el.innerHTML = `<div class="loading-spinner visible"><div class="spinner"></div><p>${msg}</p></div>`; }
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.innerHTML = `<div class="alert alert-danger">${escapeHtml(msg)}</div>`; }
}

async function apiCall(endpoint, body = {}, method = 'POST') {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (method !== 'GET') opts.body = JSON.stringify(body);
  const resp = await fetch(API_BASE + endpoint, opts);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
  return data;
}

// ─── Navigation ────────────────────────────────────────────────────────────

function switchPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const panel = document.getElementById(`panel-${name}`);
  const nav = document.querySelector(`[data-panel="${name}"]`);
  if (panel) panel.classList.add('active');
  if (nav) nav.classList.add('active');
  currentPanel = name;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-item[data-panel]').forEach(el => {
    el.addEventListener('click', () => switchPanel(el.dataset.panel));
  });

  // Set default dates
  const todayStr = today();
  const inputs = document.querySelectorAll('input[type="date"]');
  inputs.forEach(inp => { if (!inp.value) inp.value = todayStr; });

  // Check API health
  checkHealth();
  switchPanel('chat');
});

// ─── Health Check ──────────────────────────────────────────────────────────

async function checkHealth() {
  try {
    const data = await apiCall('/health', {}, 'GET');
    const dot = document.getElementById('status-dot');
    const label = document.getElementById('status-label');
    if (data.ibm_credentials_configured) {
      dot.className = 'status-dot';
      label.textContent = 'IBM Granite Connected';
    } else {
      dot.className = 'status-dot offline';
      label.textContent = 'Configure IBM Credentials';
    }
  } catch {
    document.getElementById('status-dot').className = 'status-dot offline';
    document.getElementById('status-label').textContent = 'Server Offline';
  }
}

// ─── Chat Agent ─────────────────────────────────────────────────────────────

const chatMessages = document.getElementById ? document.getElementById('chat-messages') : null;

function addMessage(role, content, suggestions = []) {
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return;

  const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const isUser = role === 'user';

  const msgHtml = `
    <div class="message ${role}">
      <div class="msg-avatar">${isUser ? '🧑' : '🤖'}</div>
      <div>
        <div class="msg-bubble">${formatMessage(content)}</div>
        <div class="msg-time">${time}</div>
      </div>
    </div>`;
  msgs.insertAdjacentHTML('beforeend', msgHtml);

  // Clear and update suggestions
  const suggestionsEl = document.getElementById('chat-suggestions');
  if (suggestionsEl && suggestions.length > 0) {
    suggestionsEl.innerHTML = suggestions.map(s =>
      `<button class="suggestion-chip" onclick="sendSuggestion('${escapeHtml(s)}')">${escapeHtml(s)}</button>`
    ).join('');
  }

  msgs.scrollTop = msgs.scrollHeight;
}

function formatMessage(text) {
  // Simple markdown-like formatting
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/•\s/g, '• ');
}

function showTyping() {
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return;
  const el = document.createElement('div');
  el.id = 'typing-indicator';
  el.className = 'message assistant';
  el.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  if (!input) return;
  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  input.style.height = 'auto';
  document.getElementById('btn-send').disabled = true;

  addMessage('user', message);
  showTyping();

  try {
    const data = await apiCall('/chat', { message, session_id: currentSessionId });
    removeTyping();
    addMessage('assistant', data.response, data.suggestions || []);
  } catch (err) {
    removeTyping();
    addMessage('assistant', `Sorry, I encountered an error: ${err.message}. Please check your IBM Cloud credentials.`);
  } finally {
    document.getElementById('btn-send').disabled = false;
    input.focus();
  }
}

function sendSuggestion(text) {
  const input = document.getElementById('chat-input');
  if (input) input.value = text;
  sendChatMessage();
}

function resetChat() {
  apiCall('/chat/reset', { session_id: currentSessionId }).catch(() => {});
  currentSessionId = 'session_' + Date.now();
  const msgs = document.getElementById('chat-messages');
  if (msgs) {
    msgs.innerHTML = '';
    addMessage('assistant',
      "Hello! I'm your IBM Travel Planner Agent powered by **IBM Granite AI**. ✈️\n\nI can help you:\n• Suggest destinations based on your preferences\n• Build detailed day-by-day itineraries\n• Check weather forecasts\n• Find transport and accommodation\n• Estimate budgets and generate packing lists\n\nWhere would you like to travel?",
      ['Suggest a destination for me', 'Plan a trip to Paris', 'What are trending destinations?', 'Help me plan a budget trip']
    );
  }
}

// ─── Destinations ──────────────────────────────────────────────────────────

async function suggestDestinations() {
  const form = document.getElementById('form-destinations');
  const result = document.getElementById('destinations-result');
  showLoading('destinations-result', 'IBM Granite is finding perfect destinations for you…');

  const body = {
    preferences: document.getElementById('dest-preferences').value,
    budget: document.getElementById('dest-budget').value,
    duration_days: parseInt(document.getElementById('dest-days').value) || 7,
    departure_from: document.getElementById('dest-from').value,
    travel_style: document.getElementById('dest-style').value,
  };

  try {
    const data = await apiCall('/destinations/suggest', body);
    if (data.error) { showError('destinations-result', data.error); return; }

    const destinations = data.destinations || [];
    if (destinations.length === 0) {
      result.innerHTML = '<div class="alert alert-warning">No destinations found. Try adjusting your preferences.</div>';
      return;
    }

    let html = `<div class="destination-grid">`;
    destinations.forEach(d => {
      const highlights = (d.highlights || []).slice(0, 3);
      const tags = (d.travel_style_tags || []).slice(0, 2);
      html += `
        <div class="destination-card" onclick="quickExplore('${escapeHtml(d.name)}')">
          <div class="dest-card-header">
            <h4>${escapeHtml(d.name)}</h4>
            <div class="dest-country">${escapeHtml(d.country || '')}</div>
          </div>
          <div class="dest-card-body">
            <p class="dest-card-why">${escapeHtml(d.why || '')}</p>
            <div class="dest-tags">
              ${tags.map(t => `<span class="dest-tag">${escapeHtml(t)}</span>`).join('')}
              ${d.visa_ease ? `<span class="dest-tag">${escapeHtml(d.visa_ease)} Visa</span>` : ''}
            </div>
            <div class="highlights-list">
              ${highlights.map(h => `<span class="highlight-tag">📍 ${escapeHtml(h)}</span>`).join('')}
            </div>
            <div class="dest-meta">
              <span>🗓 ${escapeHtml(d.best_season || 'Year-round')}</span>
              <span class="dest-budget">~$${d.estimated_budget_usd_per_day || '?'}/day</span>
            </div>
          </div>
        </div>`;
    });
    html += `</div>`;
    result.innerHTML = html;
  } catch (err) {
    showError('destinations-result', err.message);
  }
}

function quickExplore(destination) {
  document.getElementById('desc-destination').value = destination;
  switchPanel('describe');
  describeDestination();
}

async function describeDestination() {
  const destination = document.getElementById('desc-destination').value.trim();
  if (!destination) { alert('Please enter a destination'); return; }

  showLoading('describe-result', `IBM Granite is generating a guide for ${destination}…`);
  const focus = document.getElementById('desc-focus').value;

  try {
    const data = await apiCall('/destinations/describe', { destination, focus });
    const result = document.getElementById('describe-result');
    result.innerHTML = `
      <div class="card">
        <div class="card-title">📖 ${escapeHtml(destination)} — ${escapeHtml(focus)} Guide</div>
        <div style="line-height:1.8; white-space: pre-wrap;">${escapeHtml(data.description || '')}</div>
      </div>
      <div style="margin-top:1rem; display:flex; gap:8px; flex-wrap:wrap;">
        <button class="btn btn-secondary btn-sm" onclick="fetchLocalTips('${escapeHtml(destination)}')">🔍 Get Local Tips</button>
        <button class="btn btn-secondary btn-sm" onclick="prefillItinerary('${escapeHtml(destination)}')">📅 Build Itinerary</button>
        <button class="btn btn-secondary btn-sm" onclick="prefillWeather('${escapeHtml(destination)}')">🌤 Check Weather</button>
      </div>`;
  } catch (err) {
    showError('describe-result', err.message);
  }
}

async function fetchLocalTips(destination) {
  showLoading('describe-result', 'Getting insider local tips…');
  try {
    const data = await apiCall('/destinations/local-tips', { destination });
    const result = document.getElementById('describe-result');
    let html = `<div class="card"><div class="card-title">💡 Insider Tips for ${escapeHtml(destination)}</div>`;
    const sections = [
      ['hidden_gems', '💎 Hidden Gems'],
      ['local_etiquette', '🤝 Local Etiquette'],
      ['best_local_food', '🍽 Must-Try Food'],
      ['money_saving_tips', '💰 Money-Saving Tips'],
      ['safety_tips', '🛡 Safety Tips'],
      ['avoid', '⚠ Things to Avoid'],
    ];
    sections.forEach(([key, label]) => {
      const items = data[key] || [];
      if (items.length) {
        html += `<div class="packing-section"><div class="packing-section-title">${label}</div>
          <ul class="packing-list">${items.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul></div>`;
      }
    });
    html += `</div>`;
    result.innerHTML = html;
  } catch (err) {
    showError('describe-result', err.message);
  }
}

function prefillItinerary(destination) {
  document.getElementById('itin-destination').value = destination;
  switchPanel('itinerary');
}

function prefillWeather(destination) {
  document.getElementById('weather-destination').value = destination;
  switchPanel('weather');
  fetchWeather();
}

// ─── Weather ───────────────────────────────────────────────────────────────

async function fetchWeather() {
  const destination = document.getElementById('weather-destination').value.trim();
  if (!destination) { alert('Please enter a destination'); return; }
  const days = parseInt(document.getElementById('weather-days').value) || 7;

  showLoading('weather-result', `Fetching live weather for ${destination}…`);

  try {
    const data = await apiCall('/weather', { destination, days });
    if (data.error) { showError('weather-result', data.error); return; }

    const cur = data.current || {};
    const forecast = (data.forecast || []).slice(0, 7);

    let html = `
      <div class="card">
        <div class="card-title">🌤 ${escapeHtml(destination)} — Current Weather</div>
        <div class="weather-current">
          <div class="weather-stat"><div class="weather-stat-value">${escapeHtml(cur.temperature || 'N/A')}</div><div class="weather-stat-label">Temperature</div></div>
          <div class="weather-stat"><div class="weather-stat-value">${escapeHtml(cur.feels_like || 'N/A')}</div><div class="weather-stat-label">Feels Like</div></div>
          <div class="weather-stat"><div class="weather-stat-value">${escapeHtml(cur.humidity || 'N/A')}</div><div class="weather-stat-label">Humidity</div></div>
          <div class="weather-stat"><div class="weather-stat-value">${escapeHtml(cur.wind_speed || 'N/A')}</div><div class="weather-stat-label">Wind Speed</div></div>
        </div>
        <div class="alert alert-info" style="margin-bottom:1rem;">
          <strong>Condition:</strong> ${escapeHtml(cur.condition || 'Unknown')}
          ${data.timezone ? ` &nbsp;|&nbsp; <strong>Timezone:</strong> ${escapeHtml(data.timezone)}` : ''}
        </div>
        <div class="card-title">${days}-Day Forecast</div>
        <div class="forecast-grid">
          ${forecast.map(d => `
            <div class="forecast-day">
              <div class="f-date">${escapeHtml(formatDate(d.date))}</div>
              <div class="f-condition">${escapeHtml(d.condition)}</div>
              <div class="f-temps">
                <span class="f-high">↑${escapeHtml(d.max_temp)}</span>
                <span class="f-low"> ↓${escapeHtml(d.min_temp)}</span>
              </div>
              <div style="font-size:0.75rem; color:#6f6f6f; margin-top:4px;">☂ ${escapeHtml(d.precipitation)}</div>
              <div style="font-size:0.75rem; color:#6f6f6f;">UV ${escapeHtml(String(d.uv_index))}</div>
            </div>`).join('')}
        </div>
      </div>`;
    document.getElementById('weather-result').innerHTML = html;
  } catch (err) {
    showError('weather-result', err.message);
  }
}

// ─── Itinerary ─────────────────────────────────────────────────────────────

async function buildItinerary() {
  const destination = document.getElementById('itin-destination').value.trim();
  const startDate = document.getElementById('itin-start-date').value;
  if (!destination || !startDate) { alert('Please fill in destination and start date'); return; }

  const days = parseInt(document.getElementById('itin-days').value) || 7;
  showLoading('itinerary-result', `IBM Granite is building your ${days}-day ${destination} itinerary…`);

  const body = {
    destination,
    start_date: startDate,
    duration_days: days,
    preferences: document.getElementById('itin-preferences').value,
    budget: document.getElementById('itin-budget').value,
    travel_style: document.getElementById('itin-style').value,
    accommodation_type: document.getElementById('itin-accommodation').value,
    include_weather: true,
  };

  try {
    const data = await apiCall('/itinerary/build', body);
    if (data.error) { showError('itinerary-result', data.error + (data.raw_response ? `\n\nRaw: ${data.raw_response.slice(0, 200)}` : '')); return; }
    renderItinerary(data);
  } catch (err) {
    showError('itinerary-result', err.message);
  }
}

function renderItinerary(data) {
  const days = data.days || [];
  let html = `
    <div class="card" style="margin-bottom:1rem;">
      <div class="card-title">📅 ${escapeHtml(data.destination || '')} — ${data.duration_days}-Day Itinerary</div>
      <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
        <div><strong>Start:</strong> ${escapeHtml(data.start_date || '')}</div>
        <div><strong>Budget:</strong> ${escapeHtml(data.budget_level || '')}</div>
        <div><strong>Est. Total:</strong> <span style="color:var(--ibm-green);font-weight:700;">$${data.estimated_total_cost_usd || '?'}</span></div>
      </div>
    </div>`;

  days.forEach((day, i) => {
    const morning = day.morning || {};
    const afternoon = day.afternoon || {};
    const evening = day.evening || {};
    const meals = day.meals || {};

    html += `
      <div class="itinerary-day">
        <div class="day-header" onclick="toggleDay(${i})">
          <div>
            <h4>Day ${day.day || i+1} — ${escapeHtml(day.theme || '')}</h4>
            <div class="day-meta">${escapeHtml(day.date || '')} &nbsp;|&nbsp; Transport: ${escapeHtml(day.transport || 'See details')} &nbsp;|&nbsp; Budget: $${day.daily_budget_usd || '?'}</div>
          </div>
          <span id="day-chevron-${i}">▼</span>
        </div>
        <div class="day-body" id="day-body-${i}" ${i === 0 ? 'class="day-body open"' : ''}>
          ${day.weather_note ? `<div class="alert alert-info" style="margin-bottom:1rem;">☀ ${escapeHtml(day.weather_note)}</div>` : ''}
          
          ${morning.activity ? `<div class="activity-block">
            <div class="activity-time">🌅 Morning</div>
            <div class="activity-name">${escapeHtml(morning.activity)}</div>
            <div class="activity-desc">${escapeHtml(morning.description || '')} &nbsp;•&nbsp; 📍${escapeHtml(morning.location || '')} &nbsp;•&nbsp; ⏱${morning.duration_hours || '?'}h &nbsp;•&nbsp; 💵$${morning.cost_usd || '?'}</div>
            ${morning.tips ? `<div class="activity-tip">💡 ${escapeHtml(morning.tips)}</div>` : ''}
          </div>` : ''}
          
          ${afternoon.activity ? `<div class="activity-block">
            <div class="activity-time">☀ Afternoon</div>
            <div class="activity-name">${escapeHtml(afternoon.activity)}</div>
            <div class="activity-desc">${escapeHtml(afternoon.description || '')} &nbsp;•&nbsp; 📍${escapeHtml(afternoon.location || '')} &nbsp;•&nbsp; ⏱${afternoon.duration_hours || '?'}h &nbsp;•&nbsp; 💵$${afternoon.cost_usd || '?'}</div>
            ${afternoon.tips ? `<div class="activity-tip">💡 ${escapeHtml(afternoon.tips)}</div>` : ''}
          </div>` : ''}

          ${evening.activity ? `<div class="activity-block">
            <div class="activity-time">🌙 Evening</div>
            <div class="activity-name">${escapeHtml(evening.activity)}</div>
            <div class="activity-desc">${escapeHtml(evening.description || '')} &nbsp;•&nbsp; 📍${escapeHtml(evening.location || '')} &nbsp;•&nbsp; ⏱${evening.duration_hours || '?'}h &nbsp;•&nbsp; 💵$${evening.cost_usd || '?'}</div>
            ${evening.tips ? `<div class="activity-tip">💡 ${escapeHtml(evening.tips)}</div>` : ''}
          </div>` : ''}

          <div class="meal-row">
            <div><div class="meal-label">🍳 Breakfast</div>${escapeHtml(meals.breakfast || 'N/A')}</div>
            <div><div class="meal-label">🍱 Lunch</div>${escapeHtml(meals.lunch || 'N/A')}</div>
            <div><div class="meal-label">🍽 Dinner</div>${escapeHtml(meals.dinner || 'N/A')}</div>
          </div>
          ${day.accommodation ? `<div style="margin-top:0.75rem;"><strong>🏨 Stay:</strong> ${escapeHtml(day.accommodation)}</div>` : ''}
        </div>
      </div>`;
  });

  if (data.packing_tips && data.packing_tips.length > 0) {
    html += `<div class="card"><div class="card-title">🎒 Packing Tips</div>
      <ul class="packing-list">${data.packing_tips.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul></div>`;
  }

  if (data.emergency_contacts) {
    const ec = data.emergency_contacts;
    html += `<div class="card"><div class="card-title">🚨 Emergency Contacts</div>
      <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
        <span>🚔 Police: <strong>${escapeHtml(ec.police || 'N/A')}</strong></span>
        <span>🚑 Ambulance: <strong>${escapeHtml(ec.ambulance || 'N/A')}</strong></span>
        <span>📞 Tourist Help: <strong>${escapeHtml(ec.tourist_helpline || 'N/A')}</strong></span>
      </div></div>`;
  }

  document.getElementById('itinerary-result').innerHTML = html;
  // Open first day by default
  const firstBody = document.getElementById('day-body-0');
  if (firstBody) firstBody.classList.add('open');
}

function toggleDay(i) {
  const body = document.getElementById(`day-body-${i}`);
  const chevron = document.getElementById(`day-chevron-${i}`);
  if (body) {
    body.classList.toggle('open');
    if (chevron) chevron.textContent = body.classList.contains('open') ? '▲' : '▼';
  }
}

// ─── Budget ─────────────────────────────────────────────────────────────────

async function estimateBudget() {
  const destination = document.getElementById('budget-destination').value.trim();
  if (!destination) { alert('Please enter a destination'); return; }
  showLoading('budget-result', 'IBM Granite is calculating your budget…');

  const body = {
    destination,
    duration_days: parseInt(document.getElementById('budget-days').value) || 7,
    travel_style: document.getElementById('budget-style').value,
    num_travelers: parseInt(document.getElementById('budget-travelers').value) || 1,
  };

  try {
    const data = await apiCall('/itinerary/budget', body);
    if (data.error) { showError('budget-result', data.error); return; }

    const daily = data.daily_breakdown || {};
    let html = `
      <div class="card">
        <div class="card-title">💰 Budget Estimate — ${escapeHtml(data.destination || destination)}</div>
        <div style="text-align:center; margin-bottom:1.5rem;">
          <div class="budget-item-label">Estimated Total (${data.duration_days || ''} days, ${data.num_travelers || 1} traveler)</div>
          <div class="budget-total">$${data.total_estimated_usd || '?'} ${escapeHtml(data.currency || 'USD')}</div>
        </div>
        <div class="card-title">Daily Breakdown</div>
        <div class="budget-grid">
          <div class="budget-item"><div class="budget-item-value">$${daily.accommodation || '?'}</div><div class="budget-item-label">🏨 Accommodation</div></div>
          <div class="budget-item"><div class="budget-item-value">$${daily.food || '?'}</div><div class="budget-item-label">🍽 Food</div></div>
          <div class="budget-item"><div class="budget-item-value">$${daily.transport || '?'}</div><div class="budget-item-label">🚌 Transport</div></div>
          <div class="budget-item"><div class="budget-item-value">$${daily.activities || '?'}</div><div class="budget-item-label">🎭 Activities</div></div>
          <div class="budget-item"><div class="budget-item-value">$${daily.miscellaneous || '?'}</div><div class="budget-item-label">📦 Misc</div></div>
        </div>`;

    if (data.cost_of_living_note) {
      html += `<div class="alert alert-info" style="margin-top:1rem;">${escapeHtml(data.cost_of_living_note)}</div>`;
    }
    if (data.budget_tips && data.budget_tips.length) {
      html += `<div class="card-title" style="margin-top:1rem;">💡 Money-Saving Tips</div>
        <ul class="packing-list">${data.budget_tips.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>`;
    }
    html += `</div>`;
    document.getElementById('budget-result').innerHTML = html;
  } catch (err) {
    showError('budget-result', err.message);
  }
}

// ─── Transport ─────────────────────────────────────────────────────────────

async function fetchTransport() {
  const origin = document.getElementById('transport-from').value.trim();
  const destination = document.getElementById('transport-to').value.trim();
  if (!origin || !destination) { alert('Please enter origin and destination'); return; }
  showLoading('transport-result', 'IBM Granite is searching transport options…');

  const body = {
    origin, destination,
    travel_date: document.getElementById('transport-date').value,
    budget: document.getElementById('transport-budget').value,
    preferences: document.getElementById('transport-prefs').value,
  };

  try {
    const data = await apiCall('/transport', body);
    if (data.error) { showError('transport-result', data.error); return; }

    const options = data.options || [];
    let html = `<div class="card">
      <div class="card-title">🚀 Transport: ${escapeHtml(origin)} → ${escapeHtml(destination)}</div>
      ${data.recommended_option ? `<div class="alert alert-success" style="margin-bottom:1rem;">⭐ Recommended: <strong>${escapeHtml(data.recommended_option)}</strong></div>` : ''}`;

    options.forEach(opt => {
      html += `
        <div style="border:1px solid var(--border-color); border-radius:var(--radius-md); padding:1rem; margin-bottom:1rem; ${opt.recommended ? 'border-color:var(--ibm-blue);' : ''}">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <strong>${escapeHtml(opt.mode || '')} ${opt.operator ? '— ' + escapeHtml(opt.operator) : ''}</strong>
            <span style="color:var(--ibm-green); font-weight:700;">~$${opt.estimated_cost_usd || '?'}</span>
          </div>
          <div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:0.5rem;">
            ⏱ ${escapeHtml(opt.estimated_duration || 'N/A')} &nbsp;|&nbsp; Comfort: ${escapeHtml(opt.comfort_level || 'N/A')}
          </div>
          ${opt.booking_tip ? `<div class="activity-tip">🎫 ${escapeHtml(opt.booking_tip)}</div>` : ''}
          ${(opt.pros || []).length > 0 ? `<div style="margin-top:0.5rem;"><span class="badge badge-green">✓ ${(opt.pros || []).join(' &nbsp;✓ ')}</span></div>` : ''}
        </div>`;
    });

    if (data.local_transport_at_destination && data.local_transport_at_destination.length) {
      html += `<div class="card-title">🚍 Local Transport at ${escapeHtml(destination)}</div>`;
      data.local_transport_at_destination.forEach(lt => {
        html += `<div style="margin-bottom:0.5rem;"><strong>${escapeHtml(lt.mode || '')}</strong>: ${escapeHtml(lt.cost || '')} — ${escapeHtml(lt.tip || '')}</div>`;
      });
    }

    html += `</div>`;
    document.getElementById('transport-result').innerHTML = html;
  } catch (err) {
    showError('transport-result', err.message);
  }
}

// ─── Accommodation ─────────────────────────────────────────────────────────

async function fetchAccommodation() {
  const destination = document.getElementById('accom-destination').value.trim();
  if (!destination) { alert('Please enter a destination'); return; }
  showLoading('accom-result', 'IBM Granite is finding accommodation options…');

  const body = {
    destination,
    check_in: document.getElementById('accom-checkin').value,
    check_out: document.getElementById('accom-checkout').value,
    budget: document.getElementById('accom-budget').value,
    accommodation_type: document.getElementById('accom-type').value,
    num_guests: parseInt(document.getElementById('accom-guests').value) || 1,
    preferences: document.getElementById('accom-prefs').value,
  };

  try {
    const data = await apiCall('/accommodation', body);
    if (data.error) { showError('accom-result', data.error); return; }

    const recs = data.recommendations || [];
    let html = `<div class="card"><div class="card-title">🏨 Accommodation in ${escapeHtml(destination)}</div>`;

    if (data.best_areas_to_stay && data.best_areas_to_stay.length) {
      html += `<div class="alert alert-info" style="margin-bottom:1rem;">📍 Best areas: <strong>${data.best_areas_to_stay.map(a => escapeHtml(a)).join(', ')}</strong></div>`;
    }

    recs.forEach(rec => {
      html += `
        <div style="border:1px solid var(--border-color); border-radius:var(--radius-md); padding:1rem; margin-bottom:1rem;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem;">
            <div><strong>${escapeHtml(rec.name || '')}</strong> <span class="badge badge-blue">${escapeHtml(rec.type || '')}</span></div>
            <span style="color:var(--ibm-green); font-weight:700;">$${rec.estimated_price_usd_per_night || '?'}/night</span>
          </div>
          <div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:0.5rem;">
            📍 ${escapeHtml(rec.area || 'Central')} &nbsp;|&nbsp; ⭐ ${rec.rating || 'N/A'} &nbsp;|&nbsp; Book via: ${escapeHtml(rec.booking_platform || 'N/A')}
          </div>
          <div class="dest-tags">
            ${(rec.highlights || []).map(h => `<span class="dest-tag">${escapeHtml(h)}</span>`).join('')}
          </div>
        </div>`;
    });

    if (data.booking_tips && data.booking_tips.length) {
      html += `<div class="card-title" style="margin-top:0.5rem;">💡 Booking Tips</div>
        <ul class="packing-list">${data.booking_tips.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>`;
    }

    html += `</div>`;
    document.getElementById('accom-result').innerHTML = html;
  } catch (err) {
    showError('accom-result', err.message);
  }
}

// ─── Visa ───────────────────────────────────────────────────────────────────

async function fetchVisa() {
  const nationality = document.getElementById('visa-nationality').value.trim();
  const country = document.getElementById('visa-destination').value.trim();
  if (!nationality || !country) { alert('Please fill in nationality and destination country'); return; }
  showLoading('visa-result', 'IBM Granite is checking visa requirements…');

  try {
    const data = await apiCall('/visa', { nationality, destination_country: country });
    if (data.error) { showError('visa-result', data.error); return; }

    const visaColor = { 'Visa Free': 'badge-green', 'Visa on Arrival': 'badge-yellow', 'e-Visa': 'badge-blue', 'Tourist': 'badge-yellow' };
    const badgeClass = visaColor[data.visa_type] || 'badge-blue';
    const reqColor = data.visa_required ? 'badge-red' : 'badge-green';

    let html = `<div class="card">
      <div class="card-title">📋 Visa: ${escapeHtml(nationality)} → ${escapeHtml(country)}</div>
      <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1rem;">
        <span class="visa-badge ${reqColor}">${data.visa_required ? '✗ Visa Required' : '✓ Visa Free'}</span>
        <span class="visa-badge ${badgeClass}">${escapeHtml(data.visa_type || 'N/A')}</span>
        ${data.max_stay_days ? `<span class="visa-badge badge-blue">Max ${data.max_stay_days} days</span>` : ''}
        ${data.cost_usd ? `<span class="visa-badge badge-yellow">Cost: $${data.cost_usd}</span>` : ''}
      </div>
      ${data.processing_time ? `<div class="alert alert-info" style="margin-bottom:1rem;">⏱ Processing time: <strong>${escapeHtml(data.processing_time)}</strong></div>` : ''}`;

    const sections = [
      ['required_documents', '📄 Required Documents'],
      ['health_requirements', '💉 Health Requirements'],
      ['important_notes', '⚠ Important Notes'],
      ['customs_rules', '🛃 Customs Rules'],
    ];

    sections.forEach(([key, label]) => {
      const items = data[key] || [];
      if (items.length) {
        html += `<div class="packing-section"><div class="packing-section-title">${label}</div>
          <ul class="packing-list">${items.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul></div>`;
      }
    });

    if (data.application_link) {
      html += `<div style="margin-top:1rem;"><strong>🔗 Apply at:</strong> <a href="${escapeHtml(data.application_link)}" target="_blank">${escapeHtml(data.application_link)}</a></div>`;
    }

    html += `</div>`;
    document.getElementById('visa-result').innerHTML = html;
  } catch (err) {
    showError('visa-result', err.message);
  }
}

// ─── Packing List ───────────────────────────────────────────────────────────

async function generatePackingList() {
  const destination = document.getElementById('pack-destination').value.trim();
  if (!destination) { alert('Please enter a destination'); return; }
  showLoading('pack-result', 'IBM Granite is generating your packing list…');

  const body = {
    destination,
    duration_days: parseInt(document.getElementById('pack-days').value) || 7,
    climate: document.getElementById('pack-climate').value,
    activities: document.getElementById('pack-activities').value.split(',').map(s => s.trim()).filter(Boolean),
  };

  try {
    const data = await apiCall('/packing-list', body);
    if (data.error) { showError('pack-result', data.error); return; }

    let html = `<div class="card"><div class="card-title">🎒 Packing List — ${escapeHtml(destination)}</div>`;
    const sections = [
      ['essentials', '🔑 Essentials'],
      ['documents', '📋 Documents'],
      ['clothing', '👕 Clothing'],
      ['electronics', '📱 Electronics'],
      ['toiletries', '🧴 Toiletries'],
      ['medications', '💊 Medications'],
      ['activity_specific', '🏄 Activity-Specific'],
      ['money', '💳 Money & Cards'],
    ];

    sections.forEach(([key, label]) => {
      const items = data[key] || [];
      if (items.length) {
        html += `<div class="packing-section"><div class="packing-section-title">${label}</div>
          <ul class="packing-list">${items.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul></div>`;
      }
    });

    if (data.tips && data.tips.length) {
      html += `<div class="packing-section"><div class="packing-section-title">💡 Packing Tips</div>
        <ul class="packing-list">${data.tips.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul></div>`;
    }

    html += `</div>`;
    document.getElementById('pack-result').innerHTML = html;
  } catch (err) {
    showError('pack-result', err.message);
  }
}

// ─── Bookings ───────────────────────────────────────────────────────────────

async function loadBookings() {
  try {
    const data = await apiCall('/bookings', {}, 'GET');
    const bookings = data.bookings || [];
    const container = document.getElementById('bookings-list');
    if (!container) return;

    if (bookings.length === 0) {
      container.innerHTML = '<div class="alert alert-info">No bookings yet. Create your first trip booking!</div>';
      return;
    }

    container.innerHTML = bookings.map(b => `
      <div class="booking-item">
        <div class="booking-id">${escapeHtml(b.id)}</div>
        <div class="booking-info">
          <div class="booking-name">${escapeHtml(b.trip_name)}</div>
          <div class="booking-meta">📍 ${escapeHtml(b.destination)} &nbsp;|&nbsp; 
            📅 ${escapeHtml(b.start_date)} → ${escapeHtml(b.end_date)} &nbsp;|&nbsp; 
            👤 ${escapeHtml(b.traveler_name)}</div>
          ${b.alerts && b.alerts.length > 0 ? `<div class="badge badge-yellow" style="margin-top:4px;">🔔 ${b.alerts.length} alert(s)</div>` : ''}
        </div>
        <div class="booking-status status-${b.status}">${b.status}</div>
        <div style="display:flex;gap:6px;">
          <button class="btn btn-secondary btn-sm" onclick="viewBookingAlerts('${b.id}')">Alerts</button>
          ${b.status === 'confirmed' ? `<button class="btn btn-danger btn-sm" onclick="cancelBookingUI('${b.id}')">Cancel</button>` : ''}
        </div>
      </div>`).join('');
  } catch (err) {
    console.error('Failed to load bookings:', err);
  }
}

async function createBooking() {
  const body = {
    trip_name: document.getElementById('book-name').value.trim(),
    destination: document.getElementById('book-destination').value.trim(),
    start_date: document.getElementById('book-start').value,
    end_date: document.getElementById('book-end').value,
    traveler_name: document.getElementById('book-traveler').value.trim(),
    booking_type: document.getElementById('book-type').value,
  };

  if (!body.trip_name || !body.destination || !body.traveler_name) {
    alert('Please fill in all required fields'); return;
  }

  try {
    const data = await apiCall('/bookings', body);
    document.getElementById('book-form-result').innerHTML = `
      <div class="alert alert-success">✓ Booking created! ID: <strong>${data.id}</strong></div>`;
    loadBookings();
    // Clear form
    ['book-name', 'book-destination', 'book-traveler'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
  } catch (err) {
    document.getElementById('book-form-result').innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`;
  }
}

async function cancelBookingUI(id) {
  if (!confirm(`Cancel booking ${id}?`)) return;
  try {
    await apiCall(`/bookings/${id}/cancel`, {});
    loadBookings();
  } catch (err) {
    alert('Error cancelling booking: ' + err.message);
  }
}

async function viewBookingAlerts(id) {
  try {
    const data = await apiCall(`/bookings/${id}`, {}, 'GET');
    const alerts = data.alerts || [];
    if (alerts.length === 0) { alert('No alerts for this booking.'); return; }
    const msg = alerts.map(a => `[${a.type.toUpperCase()}] ${a.message} (${new Date(a.timestamp).toLocaleDateString()})`).join('\n');
    alert(`Alerts for booking ${id}:\n\n${msg}`);
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

// ─── Travel Alerts ──────────────────────────────────────────────────────────

async function fetchTravelAlerts() {
  const destination = document.getElementById('alerts-destination').value.trim();
  if (!destination) { alert('Please enter a destination'); return; }
  showLoading('alerts-result', 'IBM Granite is checking travel advisories…');

  try {
    const data = await apiCall('/alerts', {
      destination,
      travel_date: document.getElementById('alerts-date').value,
    });
    if (data.error) { showError('alerts-result', data.error); return; }

    const safetyColors = { 'Safe': 'alert-success', 'Exercise Caution': 'alert-warning', 'High Risk': 'alert-danger' };
    const safetyClass = safetyColors[data.overall_safety_level] || 'alert-info';
    const sevClass = { low: 'badge-green', medium: 'badge-yellow', high: 'badge-red' };

    let html = `<div class="card">
      <div class="card-title">🛡 Travel Alerts — ${escapeHtml(destination)}</div>
      <div class="alert ${safetyClass}" style="margin-bottom:1rem;">
        Overall Safety: <strong>${escapeHtml(data.overall_safety_level || 'Unknown')}</strong>
        ${data.natural_disaster_risk ? ` &nbsp;|&nbsp; Natural Disaster Risk: <strong>${escapeHtml(data.natural_disaster_risk)}</strong>` : ''}
      </div>`;

    const alerts = data.alerts || [];
    if (alerts.length) {
      html += `<div class="card-title">⚠ Active Alerts</div>`;
      alerts.forEach(a => {
        const cls = { low: 'alert-info', medium: 'alert-warning', high: 'alert-danger' }[a.severity] || 'alert-info';
        html += `<div class="alert ${cls}" style="margin-bottom:0.5rem;">
          <span class="badge ${sevClass[a.severity] || 'badge-blue'}">${escapeHtml(a.type || '')}</span>
          &nbsp;${escapeHtml(a.message || '')}</div>`;
      });
    }

    const sections = [
      ['health_advisories', '💉 Health Advisories'],
      ['local_laws_to_know', '⚖ Local Laws to Know'],
    ];

    sections.forEach(([key, label]) => {
      const items = data[key] || [];
      if (items.length) {
        html += `<div class="packing-section"><div class="packing-section-title">${label}</div>
          <ul class="packing-list">${items.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul></div>`;
      }
    });

    if (data.emergency_numbers) {
      const en = data.emergency_numbers;
      html += `<div class="card-title" style="margin-top:1rem;">🆘 Emergency Numbers</div>
        <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
          <span>🚔 Police: <strong>${escapeHtml(en.police || 'N/A')}</strong></span>
          <span>🚑 Ambulance: <strong>${escapeHtml(en.ambulance || 'N/A')}</strong></span>
          <span>🚒 Fire: <strong>${escapeHtml(en.fire || 'N/A')}</strong></span>
        </div>`;
    }

    html += `</div>`;
    document.getElementById('alerts-result').innerHTML = html;
  } catch (err) {
    showError('alerts-result', err.message);
  }
}

// ─── Init ───────────────────────────────────────────────────────────────────

window.addEventListener('load', () => {
  // Welcome message
  addMessage('assistant',
    "Hello! I'm your IBM Travel Planner Agent powered by **IBM Granite AI**. ✈️\n\nI can help you:\n• Suggest destinations based on your preferences\n• Build detailed day-by-day itineraries\n• Check weather forecasts\n• Find transport and accommodation\n• Estimate budgets and generate packing lists\n\nWhere would you like to travel?",
    ['Suggest a destination for me', 'Plan a trip to Paris', 'What are trending destinations?', 'Help me plan a budget trip']
  );

  // Enter key for chat
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
  }

  // Load bookings when switching to bookings panel
  document.querySelectorAll('[data-panel="bookings"]').forEach(el => {
    el.addEventListener('click', loadBookings);
  });
});


// ══════════════════════════════════════════════════════════════
// NEW FEATURES v2.0 — Templates, Currency, Agents, Streaming,
//                     Auth, PDF Download, Map
// ══════════════════════════════════════════════════════════════

// ── Auth state ────────────────────────────────────────────────
async function checkAuthState() {
  try {
    const r = await fetch('/api/auth/me', { credentials: 'include' });
    const d = await r.json();
    const label = document.getElementById('nav-auth-label');
    const item  = document.getElementById('nav-auth-item');
    if (d.authenticated && d.user && label && item) {
      label.textContent = d.user.first_name || d.user.username;
      item.onclick = () => window.location.href = '/dashboard';
      item.title   = 'View Dashboard';
    }
  } catch (e) { /* not logged in */ }
}
document.addEventListener('DOMContentLoaded', checkAuthState);

// ── Streaming chat ────────────────────────────────────────────
async function sendChatMessageStreaming() {
  const input = document.getElementById('chat-input');
  const message = (input.value || '').trim();
  if (!message) return;
  input.value = '';
  input.style.height = 'auto';
  document.getElementById('btn-send').disabled = true;

  addMessage('user', message);
  const typingEl = showTyping();
  document.getElementById('chat-suggestions').innerHTML = '';

  const streamDiv = document.createElement('div');
  streamDiv.className = 'message assistant';
  streamDiv.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div>
      <div class="msg-bubble" id="stream-bubble"></div>
      <div class="msg-time" id="stream-time"></div>
    </div>`;
  const messages = document.getElementById('chat-messages');

  try {
    const r = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ message, session_id: currentSessionId }),
    });

    removeTyping();
    messages.appendChild(streamDiv);
    const bubble = document.getElementById('stream-bubble');
    let fullText = '';

    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'chunk') {
            fullText += data.text;
            bubble.innerHTML = formatMessage(fullText);
            messages.scrollTop = messages.scrollHeight;
          } else if (data.type === 'done') {
            document.getElementById('stream-time').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            if (data.suggestions) renderSuggestions(data.suggestions);
          }
        } catch (e) { /* skip malformed */ }
      }
    }
  } catch (err) {
    removeTyping();
    addMessage('assistant', `Error: ${err.message}`);
  } finally {
    document.getElementById('btn-send').disabled = false;
    messages.scrollTop = messages.scrollHeight;
  }
}

function renderSuggestions(suggestions) {
  const container = document.getElementById('chat-suggestions');
  container.innerHTML = (suggestions || []).map(s =>
    `<button class="suggestion-chip" onclick="sendSuggestion('${s.replace(/'/g, "\\'")}')">${s}</button>`
  ).join('');
}

// Override sendChatMessage to use streaming
const _origSendChat = window.sendChatMessage;
window.sendChatMessage = sendChatMessageStreaming;

// ── Templates ─────────────────────────────────────────────────
async function loadTemplates(category = '') {
  const grid = document.getElementById('templates-grid');
  if (!grid) return;
  grid.innerHTML = '<div style="text-align:center;padding:2rem;color:var(--text-secondary)">⏳ Loading templates…</div>';
  const url = category ? `/api/templates?category=${category}` : '/api/templates';
  try {
    const d = await (await fetch(url)).json();
    const templates = d.templates || [];
    if (!templates.length) { grid.innerHTML = '<div class="alert alert-info">No templates found for this filter.</div>'; return; }
    grid.innerHTML = templates.map(t => `
      <div class="card" style="cursor:pointer;transition:transform .2s,box-shadow .2s;" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 24px rgba(0,0,0,.1)'" onmouseout="this.style.transform='';this.style.boxShadow=''">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem;">
          <span class="badge badge-blue">${t.template_category}</span>
          <span style="font-size:.78rem;color:var(--text-secondary);">❤ ${t.likes}</span>
        </div>
        <div style="font-weight:700;font-size:1rem;margin-bottom:.25rem;">${t.title}</div>
        <div style="font-size:.8rem;color:var(--text-secondary);margin-bottom:.5rem;">📍 ${t.destination} · ${t.duration_days} days · ${t.budget_level}</div>
        <div style="font-size:.82rem;color:var(--text-secondary);margin-bottom:.75rem;">${t.description}</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:.75rem;">${(t.tags||[]).map(tag => `<span class="badge badge-blue">${tag}</span>`).join('')}</div>
        <div style="font-size:.8rem;font-weight:600;color:var(--ibm-green);margin-bottom:.75rem;">~$${t.avg_cost_usd} total</div>
        <button class="btn btn-primary btn-sm" onclick="cloneTemplate('${t.id}','${t.title.replace(/'/g,"\\'")}')">📅 Use This Template</button>
      </div>`).join('');
  } catch (e) { grid.innerHTML = `<div class="alert alert-danger">Failed to load templates: ${e.message}</div>`; }
}

async function cloneTemplate(id, title) {
  try {
    const r = await fetch(`/api/templates/${id}/clone`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start_date: new Date(Date.now() + 30*86400000).toISOString().split('T')[0] })
    });
    const itinerary = await r.json();
    if (itinerary.error) { alert('Clone failed: ' + itinerary.error); return; }
    // Switch to itinerary panel and render it
    switchPanel('itinerary');
    document.getElementById('itin-destination').value = itinerary.destination || '';
    document.getElementById('itin-start-date').value  = itinerary.start_date || '';
    document.getElementById('itin-days').value         = itinerary.duration_days || 7;
    document.getElementById('itinerary-result').innerHTML = `
      <div class="alert alert-success">✓ Template "${title}" loaded! Showing preview below.</div>`;
    renderItinerary(itinerary);
  } catch (e) { alert('Error: ' + e.message); }
}

// ── Currency ──────────────────────────────────────────────────
async function convertCurrency() {
  const amount = parseFloat(document.getElementById('curr-amount').value) || 0;
  const from   = document.getElementById('curr-from').value;
  const to     = document.getElementById('curr-to').value;
  const el     = document.getElementById('currency-result-inline');
  el.textContent = '⏳';
  try {
    const d = await (await fetch('/api/currency/convert', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, from, to })
    })).json();
    if (d.error) { el.textContent = d.error; return; }
    el.textContent = `${d.from_amount} ${d.from_currency} = ${d.symbol}${d.to_amount.toLocaleString()} ${d.to_currency}`;
    el.style.color = 'var(--ibm-green)';
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

async function convertBudget() {
  const budget = parseFloat(document.getElementById('budget-usd').value) || 0;
  const el     = document.getElementById('budget-convert-result');
  el.innerHTML = '⏳ Converting…';
  try {
    const d = await (await fetch('/api/currency/budget', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget_usd: budget, currencies: ['EUR','GBP','INR','JPY','AED','AUD','CAD','SGD','THB','BRL'] })
    })).json();
    const convs = d.conversions || {};
    el.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.75rem;margin-top:.75rem;">
      ${Object.entries(convs).map(([code, info]) =>
        `<div style="background:var(--bg-secondary);border-radius:6px;padding:.75rem;text-align:center;">
          <div style="font-weight:700;font-size:.9rem;">${info.symbol}${info.amount.toLocaleString()}</div>
          <div style="font-size:.75rem;color:var(--text-secondary);">${code} · ${info.name}</div>
          <div style="font-size:.7rem;color:var(--text-secondary);">1 USD = ${info.rate} ${code}</div>
        </div>`).join('')}
    </div>`;
  } catch (e) { el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`; }
}

// ── AI Agents ─────────────────────────────────────────────────
async function loadAgentsList() {
  const el = document.getElementById('agents-list');
  if (!el) return;
  try {
    const d = await (await fetch('/api/agents/list')).json();
    el.innerHTML = (d.agents || []).map(a => `
      <div style="background:var(--bg-secondary);border-radius:8px;padding:1rem;">
        <div style="font-weight:700;font-size:.9rem;">🤖 ${a.name}</div>
        <div style="font-size:.8rem;color:var(--text-secondary);margin-top:4px;">${a.description}</div>
        <button class="btn btn-secondary btn-sm" style="margin-top:.75rem;" onclick="document.getElementById('agent-query').value='${a.description.substring(0,50).replace(/'/g,"\\'")}';document.getElementById('agent-query').focus()">Try This Agent</button>
      </div>`).join('');
  } catch (e) { /* ignore */ }
}

async function runAgent() {
  const query = document.getElementById('agent-query').value.trim();
  const el    = document.getElementById('agent-result');
  if (!query) { alert('Please enter a query.'); return; }
  el.innerHTML = '<div class="loading-spinner visible"><div class="spinner"></div><p>Running specialist agents…</p></div>';
  try {
    const d = await (await fetch('/api/agents/run', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    })).json();
    const primary = d.primary || {};
    const routing = d.routing || {};
    el.innerHTML = `
      <div class="result-section">
        <div class="result-header">
          <h3>🤖 ${routing.primary_agent || 'Agent'} Response</h3>
          <span class="badge badge-blue">Agents: ${(d.agents_used||[]).join(', ')}</span>
        </div>
        <div class="result-body">
          <div style="font-size:.8rem;color:var(--text-secondary);margin-bottom:.75rem;">Routing: ${routing.reason || ''}</div>
          <div style="line-height:1.7;">${formatMessage(primary.response || JSON.stringify(primary, null, 2))}</div>
          ${(d.supporting||[]).map(s => `<hr style="margin:1rem 0;"><div style="font-size:.8rem;color:var(--text-secondary);">Supporting (${s.agent}):</div><div style="line-height:1.7;">${formatMessage(s.response||'')}</div>`).join('')}
        </div>
      </div>`;
  } catch (e) { el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`; }
}

// ── PDF Download ──────────────────────────────────────────────
async function downloadItineraryPdf(itinerary) {
  try {
    const r = await fetch('/api/itinerary/pdf', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ itinerary })
    });
    if (!r.ok) { alert('PDF generation failed'); return; }
    const blob = await r.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `itinerary_${itinerary.destination||'trip'}.pdf`; a.click();
    URL.revokeObjectURL(url);
  } catch (e) { alert('PDF error: ' + e.message); }
}

// ── Init new panels when switched to ─────────────────────────
const _origSwitchPanel = window.switchPanel;
window.switchPanel = function(name) {
  _origSwitchPanel && _origSwitchPanel(name);
  if (name === 'templates') loadTemplates();
  if (name === 'agents')    loadAgentsList();
};

