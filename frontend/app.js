// NOTE: this expects your FastAPI /weather response shaped like:
// { "city": "Kyiv", "temperature": 21.5, "feels_like": 20.0,
//   "humidity": 60, "wind_speed": 3.4, "description": "clear sky" }
// and /history like:
// [{ "city": "Kyiv", "temperature": 21.5, "requested_at": "2026-08-01T12:00:00Z" }, ...]
// If your backend fields are named differently, either adjust the field
// names below or adjust your Pydantic response model to match.

const cityInput = document.getElementById('city-input');
const searchBtn = document.getElementById('search-btn');
const btnText = document.getElementById('btn-text');
const btnSpinner = document.getElementById('btn-spinner');
const errorBox = document.getElementById('error');
const resultBox = document.getElementById('result');
const historyBtn = document.getElementById('history-btn');
const historyBox = document.getElementById('history');

let historyVisible = false;

function iconFor(description) {
  const d = (description || '').toLowerCase();
  if (d.includes('storm') || d.includes('thunder')) return '⛈️';
  if (d.includes('snow')) return '❄️';
  if (d.includes('rain') || d.includes('drizzle')) return '🌧️';
  if (d.includes('mist') || d.includes('fog') || d.includes('haze')) return '🌫️';
  if (d.includes('cloud')) return '☁️';
  if (d.includes('clear')) return '☀️';
  return '🌤️';
}

function setLoading(isLoading) {
  searchBtn.disabled = isLoading;
  btnText.classList.toggle('hidden', isLoading);
  btnSpinner.classList.toggle('hidden', !isLoading);
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove('hidden');
  resultBox.classList.add('hidden');
}

function hideError() {
  errorBox.classList.add('hidden');
}

function showResult(data) {
  document.getElementById('result-icon').textContent = iconFor(data.description);
  document.getElementById('result-temp').textContent = `${Math.round(data.temperature)}°C`;
  document.getElementById('result-city').textContent = data.city;
  document.getElementById('result-desc').textContent = data.description || '';
  document.getElementById('result-feels').textContent = `${Math.round(data.feels_like)}°C`;
  document.getElementById('result-humidity').textContent = `${data.humidity}%`;
  document.getElementById('result-wind').textContent = `${data.wind_speed} м/с`;
  resultBox.classList.remove('hidden');
}

async function fetchWeather() {
  const city = cityInput.value.trim();
  if (!city) {
    showError('Введіть назву міста');
    return;
  }

  hideError();
  setLoading(true);

  try {
    const res = await fetch(`/weather?city=${encodeURIComponent(city)}`);

    if (res.status === 404) {
      showError('Місто не знайдено. Перевірте написання.');
      return;
    }
    if (!res.ok) {
      showError('Помилка сервера. Спробуйте пізніше.');
      return;
    }

    const data = await res.json();
    showResult(data);
  } catch (err) {
    showError('Не вдалося з\'єднатись з сервером.');
    console.error(err);
  } finally {
    setLoading(false);
  }
}

async function toggleHistory() {
  historyVisible = !historyVisible;

  if (!historyVisible) {
    historyBox.classList.add('hidden');
    historyBtn.textContent = 'Історія запитів';
    return;
  }

  historyBtn.textContent = 'Сховати історію';
  historyBox.innerHTML = 'Завантаження...';
  historyBox.classList.remove('hidden');

  try {
    const res = await fetch('/history');
    if (!res.ok) throw new Error('Failed to load history');
    const items = await res.json();

    if (!items.length) {
      historyBox.innerHTML = '<div class="history-item"><span>Історія порожня</span></div>';
      return;
    }

    historyBox.innerHTML = items
      .map(item => {
        const time = item.requested_at
          ? new Date(item.requested_at).toLocaleString('uk-UA')
          : '';
        return `<div class="history-item"><span>${item.city} — ${Math.round(item.temperature)}°C</span><span>${time}</span></div>`;
      })
      .join('');
  } catch (err) {
    historyBox.innerHTML = '<div class="history-item"><span>Не вдалося завантажити історію</span></div>';
    console.error(err);
  }
}

searchBtn.addEventListener('click', fetchWeather);
cityInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') fetchWeather();
});
historyBtn.addEventListener('click', toggleHistory);
