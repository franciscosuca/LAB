# QR Photo Bridge

A sample Electron desktop app that pairs with your phone over your local
Wi‑Fi network using a QR code. Scan it with your phone's camera, take (or
choose) a photo in the mobile browser, and it shows up on the desktop app
instantly — no cables, no accounts, no cloud service.

## How it works

```
┌────────────────────┐        LAN (same Wi-Fi)        ┌───────────────────────┐
│   Desktop (Electron)│ ───────────────────────────── │   Phone (browser)      │
│                      │                                │                       │
│  main.js             │  1. Shows QR code encoding     │  mobile.html/js       │
│  ├─ starts an Express │     http://<lan-ip>:port/m/id │  ├─ opens the link    │
│  │  + WebSocket server│                                │  ├─ opens WebSocket   │
│  ├─ generates a random│  2. Phone opens the link and  │  │  -> "I'm connected"│
│  │  session id + QR   │     connects a WebSocket       │  ├─ takes a photo     │
│  └─ renderer shows the│     ("phone connected" status) │  │  (native camera or │
│     live gallery      │  3. Phone POSTs the photo       │  │  live preview)    │
│                      │ ◀───────────────────────────── │  └─ uploads it (POST) │
└────────────────────┘  4. Desktop shows it instantly    └───────────────────────┘
```

- **Pairing / "session" mechanism**: on launch (and whenever you click **New
  session**), the desktop app generates a random, unguessable session id and
  builds a URL like `http://192.168.1.23:17321/m/<sessionId>`. That URL is
  encoded as a QR code. The session id acts as a bearer token/capability: only
  someone who has scanned the QR (or been given the link) can upload to that
  session, and it automatically expires after 30 minutes or when you start a
  new session.
- **Realtime status**: once the phone opens the link, it opens a WebSocket
  back to the desktop's embedded server, which flips the desktop UI to "Phone
  connected". The same channel lets the desktop send a "please take a photo"
  nudge back to the phone (best-effort remote shutter).
- **Photo transfer**: the phone uploads the photo as a normal
  `multipart/form-data` POST to the desktop's embedded HTTP server. The
  desktop saves it to disk and pushes it to the UI over Electron IPC — no
  internet connection or third-party service involved, everything stays on
  your local network.
- **Camera access on the phone**: the mobile page defaults to
  `<input type="file" accept="image/*" capture="environment">`, which opens
  the phone's native camera UI and works reliably over plain HTTP on both iOS
  and Android. If the page happens to be loaded in a "secure context" (e.g.
  `https://` or `localhost`), it progressively upgrades to a live
  `getUserMedia` camera preview with an in-page shutter button instead.

## Project structure

```
src/
├── main/
│   ├── main.js       # Electron entry point, window + IPC wiring
│   ├── preload.js    # contextBridge API exposed to the renderer
│   ├── server.js      # Express + WebSocket pairing/upload server
│   └── network.js     # LAN IP address discovery
├── renderer/           # Desktop UI (QR code, status, photo gallery)
│   ├── index.html
│   ├── renderer.js
│   └── styles.css
└── mobile/             # Page served to the phone when it scans the QR
    ├── mobile.html
    ├── mobile.js
    └── mobile.css
```

## Requirements

- macOS or Windows 10/11.
  - macOS: built and verified end-to-end (see below) on Apple Silicon,
    macOS Sequoia/Sonoma and newer; Intel Macs work too.
  - Windows: the steps below are provided for reference but have **not**
    been executed on an actual Windows machine (this project was developed
    and tested on macOS only). The app itself uses only cross-platform
    Electron/Node/Express/browser APIs, so it should work as-is, but please
    treat the Windows section as unverified.
- [Node.js](https://nodejs.org/) 18+ (Node 24 was used to build this).
- Your desktop and your phone connected to **the same Wi‑Fi network** (a
  guest network with "client/AP isolation" enabled will *not* work — see
  Troubleshooting).

## Setup

```bash
npm install
```

This installs Electron plus the small server-side dependencies (`express`,
`ws`, `multer`, `qrcode`).

> **Note:** `npm install` may finish without the ~130MB Electron binary
> actually downloaded yet (it's fetched lazily on first run instead). If so,
> the very first `npm start` will print `Downloading Electron binary...`
> before the window opens — that's expected and only happens once. If it
> ever gets interrupted, just re-run `npm start`, or force it manually with
> `node node_modules/electron/install.js`.

## Run it

Both platforms use the exact same commands:

```bash
npm start
```

A window titled **QR Photo Bridge** opens showing a QR code and a link.

### macOS ✅ verified

Because the app opens a local server so your phone can reach it, macOS may
show a firewall prompt such as:

> *"Do you want the application 'Electron' to accept incoming network
> connections?"*

Click **Allow**. If you accidentally click "Deny", go to
**System Settings → Network → Firewall → Options…** and allow incoming
connections for Electron (or turn the setting on for it), then restart the
app.

### Windows ⚠️ unverified — steps provided, not executed on a real Windows machine

Commands are identical to macOS:

```powershell
npm install
npm start
```

- **Windows Defender Firewall.** The first time the app starts its local
  server, Windows shows a *"Windows Defender Firewall has blocked some
  features of this app"* dialog. In dev mode it will usually name the app
  **Electron** (the executable is `node_modules\electron\dist\electron.exe`),
  not "QR Photo Bridge" — that's expected. Check the **Private networks**
  box and click **Allow access**; leave **Public networks** unchecked unless
  you specifically need it. If you dismiss/miss the prompt, open
  **Windows Security → Firewall & network protection → Allow an app through
  firewall → Change settings**, find **Electron** (or **Node.js**) in the
  list, and enable it for **Private** networks.
- **Network profile.** Windows blocks inbound connections regardless of
  firewall app rules if your Wi‑Fi connection is set to the **Public**
  profile. Go to **Settings → Network & Internet → Wi‑Fi → (your network) →
  Network profile type** and switch it to **Private** so the phone can
  reach the app.
- **Third-party antivirus.** Suites such as Norton/McAfee/Kaspersky layer
  their own firewall on top of Windows'; if the phone still can't connect
  after allowing the app through Windows Firewall, check the antivirus
  app's network/firewall settings too.
- **PowerShell execution policy.** If `npm install`/`npm start` fails with
  *"running scripts is disabled on this system"*, either run the commands
  from **Command Prompt (cmd.exe)** instead of PowerShell, or allow npm's
  scripts once with:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
- **Corporate proxy.** If the Electron binary can't download from behind a
  proxy, configure npm first:
  ```powershell
  npm config set proxy http://<proxy-host>:<port>
  npm config set https-proxy http://<proxy-host>:<port>
  ```
  or point Electron at an internal mirror with the `ELECTRON_MIRROR`
  environment variable.
- **Run it natively, not inside WSL.** Use a native PowerShell/Command
  Prompt terminal rather than a WSL (Linux) shell — the Electron window
  needs a real Windows display session, and the embedded server needs to
  bind to the actual Windows network adapter your phone can reach (WSL runs
  behind its own virtual/NAT adapter).
- Received photos are saved under
  `%APPDATA%\QR Photo Bridge\received-photos\<sessionId>\` (typically
  `C:\Users\<you>\AppData\Roaming\QR Photo Bridge\received-photos\`).

### Pair your phone

1. Make sure your phone is on the same Wi‑Fi network as your computer.
2. Open the Camera app (or any QR scanner) on your phone and scan the QR code
   shown in the desktop window.
3. Tap the notification/link to open it in your browser. The desktop status
   pill turns into **"Phone connected"**.
4. Tap **Open camera**, take a photo, then **Send to desktop**.
5. The photo appears instantly in the desktop app's gallery.

### Testing without a phone

Click **"Test with this computer"** in the desktop app — it opens the same
pairing page in your default browser using `127.0.0.1` instead of your LAN
IP. Browsers treat `localhost`/`127.0.0.1` as a secure context, so this path
lets you exercise the full live-camera (`getUserMedia`) flow using this
computer's own webcam, which is handy for development.

### Other features

- **New session** — rotates to a fresh, random session id/QR code and
  invalidates the old link.
- **Network interface selector** — appears if your computer has more than
  one active network adapter (e.g. Wi‑Fi and Ethernet, or a VPN's virtual
  adapter); pick the one your phone can actually reach.
- **"Ask phone for a photo"** — sends a nudge to the connected phone over the
  WebSocket. If the phone already has its live camera preview open, it
  captures and uploads automatically; otherwise it just prompts/vibrates the
  phone to remind the user.
- **Open photos folder / Show in folder** — received photos are saved to:
  - macOS: `~/Library/Application Support/QR Photo Bridge/received-photos/<sessionId>/`
  - Windows: `%APPDATA%\QR Photo Bridge\received-photos\<sessionId>\`

## Troubleshooting

- **Phone can't open the link / times out.** Almost always a networking
  issue, not the app:
  - Confirm both devices show the same Wi‑Fi network name.
  - Coffee-shop/office/guest Wi‑Fi networks often enable "client isolation",
    which blocks devices from reaching each other even on the same SSID —
    use a home network or a personal hotspot instead.
  - Check the network selector in the app; pick the adapter that matches your
    Wi‑Fi (avoid VPN/virtual adapters).
  - Re-check the firewall prompt described above (macOS Application
    Firewall, or Windows Defender Firewall + network profile on Windows).
- **QR won't scan.** Use the "Copy" button next to the link and paste/send it
  to the phone manually (e.g. Messages/AirDrop) as a fallback.
- **Live camera preview never shows up on the phone**, only "Open camera".
  This is expected over `http://<lan-ip>` — mobile browsers only allow
  `getUserMedia` in secure contexts (HTTPS or localhost). The file/camera
  input fallback is intentional so the app works reliably without setting up
  TLS certificates. See "Possible extensions" below if you want live preview
  over the LAN too.

## Security notes (this is a sample/demo app)

- The server binds to all interfaces (`0.0.0.0`) so it's reachable from your
  LAN — anyone on the same network who obtains a still-valid session link
  could upload a photo to that session. Sessions are random (72-bit) and
  expire after 30 minutes, and rotating via "New session" immediately
  invalidates the old one, but there's no additional authentication layer.
  Don't expose this port to the public internet.
- Uploads are limited to image mime types and 20MB per file.
- Everything stays on your LAN — there is no cloud/relay server involved.

## Possible extensions

- Serve over HTTPS with a locally-trusted certificate (e.g.
  [mkcert](https://github.com/FiloSottile/mkcert)) so the live `getUserMedia`
  preview works on the phone too, not just on `localhost`.
- Use a tunneling service (e.g. ngrok/Cloudflare Tunnel) if your phone and
  desktop aren't on the same network.
- Package the app for distribution with `electron-builder`/`electron-forge`.
- Persist session/photo history across restarts, add drag-out-to-Finder for
  received photos, strip EXIF metadata, etc.
