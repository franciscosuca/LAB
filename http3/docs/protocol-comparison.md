# HTTP/2 vs HTTP/3: what's actually different, and how to see it

This is the "why" behind the numbers `httpbench` produces. It's written to be
read alongside actually running the tool - each section ends with how to
reproduce the effect it describes.

## 1. The stacks

```
HTTP/2:   HTTP/2  ->  TLS 1.2/1.3  ->  TCP  ->  IP
HTTP/3:   HTTP/3  ->  QUIC (TLS 1.3 built in)  ->  UDP  ->  IP
```

HTTP/2 (originally RFC 7540, revised as RFC 9113) added request multiplexing
on top of a single TCP connection: many logical "streams" interleaved as
frames on one byte stream. That fixed HTTP/1.1's problem (one request in
flight per connection, or ugly workarounds like domain sharding) but
inherited TCP's guarantees - and TCP guarantees **strictly ordered, complete
delivery of one byte stream**. That guarantee is the root of everything
HTTP/3 changes.

HTTP/3 (RFC 9114) keeps HTTP/2's idea of multiplexed streams, but reimplements
the transport from scratch as QUIC (RFC 9000, with TLS 1.3 integration
defined in RFC 9001, and loss recovery/congestion control in RFC 9002) on top
of UDP. Header compression moved from HPACK (RFC 7541) to QPACK (RFC 9204),
adapted so header decompression doesn't itself get blocked by loss on
unrelated streams.

## 2. Head-of-line blocking: the headline reason QUIC exists

In HTTP/2, streams are a framing convention *on top of* one TCP connection.
TCP doesn't know streams exist - it just guarantees "this byte stream will be
delivered in order, with nothing missing." If packet #5 out of #1-10 is lost:

```
TCP:   [1][2][3][4][ 5 LOST ][6][7][8][9][10]
                       ^
       packets 6-10 already arrived, but TCP withholds ALL of them
       from the application until #5 is retransmitted and arrives.

HTTP/2 streams A, B, C multiplexed over those bytes: even if the lost
packet only contained data for stream A, streams B and C are also stuck
waiting - the application can't see any of the bytes after the gap until
TCP resequences everything.
```

QUIC streams are independent **at the transport layer**: each stream has its
own delivery order, and loss recovery operates per-stream (with connection-
level flow control on top, but no connection-wide ordering requirement).

```
QUIC:  stream A: [1][2][3 LOST][4]     -> stream A stalls until #3 arrives
       stream B: [1][2][3][4][5]       -> unaffected, delivered immediately
       stream C: [1][2][3][4]          -> unaffected, delivered immediately
```

This is *transport-level* HOL blocking elimination. It says nothing about
application-level HOL blocking (e.g. if your API's stream B response
logically depends on stream A's response) - QUIC can't fix that, only your
application design can.

**See it in `httpbench`:** the `concurrency` scenario fires many requests
over one connection. On a clean loopback link there's ~0 packet loss, so this
difference won't show up - HTTP/2 already multiplexes fine when nothing is
lost. Add loss to make it visible:

```bash
httpbench bench --scenarios concurrency --concurrency 50 --loss 0    # baseline
httpbench bench --scenarios concurrency --concurrency 50 --loss 3 --delay 40  # induced loss
```

Compare the p99 total-time column between the two runs, per protocol. HTTP/2
should degrade noticeably more than HTTP/3 as loss increases - and the gap
should widen as `--concurrency` increases (more streams sharing the one lossy
TCP connection).

## 3. Handshakes: fewer round trips before the first byte

- **HTTP/2 over TLS 1.2**: TCP handshake (1 RTT) then TLS 1.2 handshake
  (typically 2 RTTs) before the first HTTP byte - roughly 3 RTTs cold.
- **HTTP/2 over TLS 1.3**: TCP handshake (1 RTT) then TLS 1.3 handshake
  (1 RTT) - roughly 2 RTTs cold. With TLS 1.3 session resumption (0-RTT
  data), a *repeat* connection can send application data immediately after
  the TCP handshake, at the cost of replay-attack exposure for that early
  data (not commonly enabled for arbitrary requests).
- **HTTP/3 / QUIC**: the transport and crypto handshakes are the same
  handshake - QUIC packets carry the TLS 1.3 ClientHello/ServerHello
  directly. A fresh connection is 1 RTT to the first byte; a *repeat*
  connection to a server QUIC has seen before can use 0-RTT (send request
  data in the very first flight), with the same replay caveats as TLS 1.3
  0-RTT.

On a fast local network the difference between "2 RTT" and "1 RTT" is a
couple of milliseconds - forgettable. On a mobile connection with 150-300ms
RTT to the server, saving one full round trip is 150-300ms **on every new
connection**, which is a real, user-visible effect on page-load and API
cold-start latency.

**See it in `httpbench`:** the `cold_start` scenario opens a brand-new
connection per request and measures time to first byte. It's most
interesting when you add artificial latency:

```bash
httpbench bench --scenarios cold_start --delay 80     # ~simulates a mobile RTT
```

Note the asymmetry documented in the main README: for HTTP/2, `cold_start`'s
`total_ms` already *is* "connection + first byte" (httpx doesn't expose a
separate handshake timer). For HTTP/3, `connect_ms` in `results.csv` is the
QUIC handshake alone, measured directly - a bonus number, not required to
make the comparison fair.

## 4. Connection migration

A TCP connection is identified by a 4-tuple: (source IP, source port,
destination IP, destination port). Change your IP address - say, a phone
moving from wifi to cellular - and every open TCP connection breaks; every
protocol on top (including HTTP/2) has to reconnect and redo the handshake.

QUIC connections are identified by a **connection ID** that's independent of
the network path. A client can switch networks and keep using the same QUIC
connection (after a short validation exchange) instead of reconnecting from
scratch. `httpbench` doesn't simulate network switching (it would need
multi-interface plumbing beyond a benchmark CLI's scope) - this is a real
advantage you'd only observe on an actual mobile client changing networks
mid-session, not something to expect to see on a laptop hitting loopback.

## 5. Congestion control and flow control

TCP's congestion control lives in the OS kernel: heavily optimized, hardware
offload where available (segmentation offload, checksum offload), but harder
to evolve and identical for every application on the machine. QUIC's
congestion control lives in userspace, in the library/application - easier to
iterate on (new algorithms ship with library updates, not kernel updates) and
per-connection tunable, but it means QUIC does more work per byte in
userspace that TCP mostly does in the kernel.

QUIC also has flow control **per stream** in addition to per-connection, so
one slow-reading stream can't starve others of receive buffer the way it can
be trickier to reason about with raw TCP sockets multiplexed by an
application protocol.

**See it (indirectly) in `httpbench`:** the `payload_sweep` scenario
downloads increasing sizes. On loopback, throughput is dominated by CPU/memcpy
cost, not congestion control - so this is more about observing that HTTP/3's
userspace processing has *some* CPU cost per byte, which is point 6 below.

## 6. Advantages and disadvantages, summarized

### HTTP/3 advantages

- **No transport-level head-of-line blocking** - independent QUIC streams
  (see §2).
- **Faster connection establishment** - handshake combines transport+crypto
  into 1-RTT, with optional 0-RTT resumption (see §3).
- **Connection migration** - survives client IP changes via connection IDs
  (see §4).
- **Mandatory, always-on encryption** - QUIC has no cleartext mode; even
  transport-layer metadata (packet numbers, ACK timing) is protected, which
  also reduces "protocol ossification" from middleboxes that historically
  interfered with evolving TCP.
- **More flexible, per-stream flow control and pluggable congestion control**
  (see §5).

### HTTP/3 disadvantages

- **More CPU per byte.** Userspace packet processing (no kernel/NIC offload
  historically, though GSO/GRO and kernel-QUIC support are improving this)
  means HTTP/3 can cost more CPU than HTTP/2 at high throughput, particularly
  on servers terminating many connections.
- **UDP is sometimes blocked or deprioritized.** Corporate firewalls, some
  VPNs, and some public wifi networks block or throttle UDP, which is why
  HTTP/3 deployments always need an HTTP/2 (or 1.1) fallback (advertised via
  the `Alt-Svc` header, which is also how `httpbench bench` auto-discovers
  the HTTP/3 port).
- **Younger ecosystem.** Standardized in 2021 (RFC 9000/9114); tooling,
  observability, and battle-testing are newer than TCP's decades of
  production hardening. This project itself is a good example: there's no
  mature high-level HTTP/3 client analogous to `requests`/`httpx` for
  HTTP/2 - `aioquic` (what this project uses) operates at a much lower,
  event-driven level.
- **More implementation surface = more room for bugs/attack surface**,
  simply because congestion control, retransmission, flow control, and
  multiplexing all moved from (very mature) kernel TCP stacks into
  (comparatively young) userspace libraries.
- **Harder to passively observe/debug on the wire** for network operators,
  since QUIC encrypts more than TCP+TLS does (arguably a privacy *advantage*,
  but an operational complication for traditional network monitoring/
  troubleshooting tooling built around plaintext TCP headers).

### HTTP/2 advantages (i.e., why not just always use HTTP/3)

- **Ubiquitous, mature, boring-in-a-good-way.** Every proxy, load balancer,
  corporate firewall, and piece of network tooling understands TCP.
- **Lower CPU overhead** in the common case, since the OS kernel (and often
  NIC hardware) handles segmentation, checksums, and congestion control.
- **Works on networks that block/throttle UDP** without any fallback logic.
- **Easier to debug** with decades-old, ubiquitous tools (tcpdump, Wireshark)
  against plaintext TCP headers (the TLS payload is still encrypted, but
  connection-level behavior is easier to observe).

## 7. Honest limitations of this project's benchmarks

- **Loopback has ~0 RTT and ~0% loss.** Most of §2-§4's advantages need real
  network conditions to show up; that's exactly why `--loss`/`--delay`
  exist. Even with them, `tc netem` on `lo` is a rough approximation of a
  real lossy/high-latency path, not a perfect simulation.
- **One machine runs both the client and the server** (in `quickstart`, even
  the same process). CPU contention between the benchmark client and the
  server-under-test is a real confound at high concurrency/throughput -
  results will be noisier than a proper two-host benchmark.
- **Small, synthetic payloads.** The demo API returns predictable, compressible-
  looking filler bytes, not representative production response bodies (JSON
  payloads, images, etc.). Use `httpbench bench --host <real API>` against a
  real service for a realistic picture.
- **Congestion control needs sustained transfer + real bandwidth constraints
  to matter.** `payload_sweep`'s largest default size (1MB) on loopback
  finishes before congestion control meaningfully kicks in either protocol.

## 8. Adding HTTP/3 to your own API

If `httpbench bench --host your-api.example.com` fails because your API only
speaks HTTP/2, common ways to add HTTP/3:

- **Put it behind a CDN/edge network that already terminates HTTP/3** -
  Cloudflare, Fastly, and (for AWS) CloudFront all support HTTP/3 at the
  edge; your origin keeps speaking HTTP/1.1 or HTTP/2 behind them. This is by
  far the most common way HTTP/3 gets adopted in practice.
- **Terminate it yourself** with a server that supports HTTP/3 directly:
  Caddy (automatic, on by default), nginx (1.25+, built with the QUIC
  module), HAProxy (3.x+), or - as this project demonstrates - Hypercorn in
  front of any ASGI app (`httpbench`'s own demo server *is* a working example
  of this).
- Either way, verify it with [http3check.net](https://http3check.net/) or
  `httpbench bench --host your-api.example.com --port 443 --protocols HTTP/3`
  before relying on it.

## Further reading

- RFC 9000 - QUIC: A UDP-Based Multiplexed and Secure Transport
- RFC 9001 - Using TLS to Secure QUIC
- RFC 9002 - QUIC Loss Detection and Congestion Control
- RFC 9114 - HTTP/3
- RFC 9204 - QPACK: Field Compression for HTTP/3
- RFC 9113 - HTTP/2 (current revision; originally RFC 7540)
