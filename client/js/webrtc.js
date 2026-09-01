export function createPeerConnection(onTrack) {
  const pc = new RTCPeerConnection({
    iceServers: [],
  });

  pc.ontrack = (event) => {
    if (event.streams.length > 0) {
      onTrack(event.streams[0]);
    }
  };

  return pc;
}

export async function createViewerOffer(pc) {
  pc.addTransceiver('video', { direction: 'recvonly' });
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  return pc.localDescription;
}
