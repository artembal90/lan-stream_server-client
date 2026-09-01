# Stage 2 validation

## Software path implemented

`mss` captures the selected monitor, frames are converted to `VideoFrame`, `aiortc` publishes the media track, and the source prefers H.264. The browser creates a recv-only WebRTC transceiver and waits for ICE gathering before sending its SDP offer.

## Manual LAN validation

Run the server:

```text
python -m server.app.main
```

Run the source on Windows:

```text
python -m source.app.main --server http://<SERVER-IP>:8080 --name "Desktop" --width 1280 --height 720 --fps 30
```

Open `http://<SERVER-IP>:8080/` in the receiver browser and select the source.

Record:

- browser decoded FPS;
- browser received bitrate;
- browser RTT;
- source CPU percentage;
- source RAM usage;
- end-to-end visual latency.

Repeat at 1280x720/30 and 1920x1080/30, then 1920x1080/60 where the source hardware can sustain capture.

## Important limitation

Repository automation can validate the Python/server smoke tests, but it cannot measure Windows desktop capture, GPU/CPU load, browser rendering, or real LAN end-to-end latency. Those values must be measured on the target Windows source and receiver PCs.
