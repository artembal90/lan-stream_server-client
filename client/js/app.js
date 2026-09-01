import { createPeerConnection, createViewerOffer } from './webrtc.js';

const app = document.querySelector('#app');
app.innerHTML = `
  <section>
    <h1>LAN Stream</h1>
    <button id="refresh">Обновить список</button>
    <div id="sources"></div>
    <div id="grid"></div>
  </section>
`;

const sourcesElement = document.querySelector('#sources');
const grid = document.querySelector('#grid');
const serverBase = `${window.location.protocol}//${window.location.host}`;

async function loadSources() {
  const response = await fetch(`${serverBase}/api/sources`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  sourcesElement.replaceChildren();
  for (const source of data.sources ?? []) {
    const button = document.createElement('button');
    button.textContent = `Подключить: ${source.name} (${source.width}x${source.height} @ ${source.fps})`;
    button.onclick = () => connectSource(source.source_id, source.name);
    sourcesElement.append(button);
  }
}

async function connectSource(sourceId, name) {
  const tile = document.createElement('section');
  tile.innerHTML = `<h2>${name}</h2><video autoplay playsinline controls></video><pre class="stats">connecting...</pre>`;
  grid.append(tile);
  const video = tile.querySelector('video');
  const statsElement = tile.querySelector('.stats');

  const peerId = `viewer-${crypto.randomUUID()}`;
  const pc = createPeerConnection((stream) => { video.srcObject = stream; });
  const ws = new WebSocket(`${serverBase.replace(/^http/, 'ws')}/ws?peer_id=${encodeURIComponent(peerId)}`);
  const offer = await createViewerOffer(pc);

  ws.onopen = () => ws.send(JSON.stringify({
    type: 'offer', target: sourceId, session_id: sourceId, sdp: offer.sdp, sdp_type: offer.type,
  }));

  ws.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'answer') {
      await pc.setRemoteDescription({ type: message.sdp_type ?? 'answer', sdp: message.sdp });
    }
  };

  const timer = setInterval(async () => {
    if (pc.connectionState === 'closed' || pc.connectionState === 'failed') {
      clearInterval(timer);
      return;
    }
    const reports = await pc.getStats();
    for (const report of reports.values()) {
      if (report.type === 'inbound-rtp' && report.kind === 'video') {
        const kbps = report.bytesReceived ? Math.round((report.bytesReceived * 8) / 1000) : 0;
        statsElement.textContent = `state: ${pc.connectionState}\ncodec: ${report.codecId ?? 'n/a'}\nreceived: ${kbps} kb\nframes: ${report.framesReceived ?? 0} (decoded ${report.framesDecoded ?? 0})`;
      }
      if (report.type === 'candidate-pair' && report.state === 'succeeded' && report.currentRoundTripTime != null) {
        statsElement.textContent += `\nrtt: ${Math.round(report.currentRoundTripTime * 1000)} ms`;
      }
    }
  }, 1000);
}

document.querySelector('#refresh').onclick = () => loadSources().catch(showError);
loadSources().catch(showError);

function showError(error) { sourcesElement.textContent = `Ошибка: ${error.message}`; }
