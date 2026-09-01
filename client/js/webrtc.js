function waitForIceGatheringComplete(pc) {
  if (pc.iceGatheringState === 'complete') return Promise.resolve();
  return new Promise((resolve) => {
    const check = () => {
      if (pc.iceGatheringState === 'complete') {
        pc.removeEventListener('icegatheringstatechange', check);
        resolve();
      }
    };
    pc.addEventListener('icegatheringstatechange', check);
  });
}

export function createPeerConnection(onTrack) {
  const pc = new RTCPeerConnection({ iceServers: [] });
  pc.ontrack = (event) => {
    if (event.streams.length > 0) onTrack(event.streams[0]);
  };
  return pc;
}

export async function createViewerOffer(pc) {
  pc.addTransceiver('video', { direction: 'recvonly' });
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  await waitForIceGatheringComplete(pc);
  return pc.localDescription;
}
