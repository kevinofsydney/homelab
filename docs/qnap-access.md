# QNAP management access

QTS's built-in certificate does not match the address it is reached at, so browsers warn and some (including the Claude desktop app's built-in browser) refuse to load it. Since 2026-10-28 QTS is also published on the tailnet with a valid certificate.

## Setup (2026-10-28, owner-approved)

1. Tailscale admin console → DNS → **HTTPS Certificates** → Enable. MagicDNS was already on. Certificates are recorded in public Certificate Transparency logs, so the NAS's tailnet name becomes publicly visible; nothing becomes reachable from the internet.
2. On the QNAP, over SSH as the owner's admin account:

   ```bash
   /share/CACHEDEV1_DATA/.qpkg/Tailscale/tailscale serve --bg --https=8443 https+insecure://127.0.0.1:443
   ```

   Port 8443 avoids QTS's own 443. Tailscale obtains and renews a Let's Encrypt certificate for the NAS's tailnet name and proxies to QTS locally.

Verified: the served certificate's subject is the NAS's tailnet name, issued by Let's Encrypt (`YE2`), valid to 2027-01-26; QTS answered HTTP 200 and its login page loaded in the built-in browser.

## Use

Open `https://<nas tailnet name>:8443` from a tailnet device. The actual name is in the Tailscale admin console's machine list.

## Known issues

- **Windows name resolution on the operator PC (Titan):** Tailscale's resolver answered the NAS name correctly (`tailscale dns query`), but Windows lookups through `100.100.100.100` returned only a `ts.net` SOA, likely because the tailnet's NextDNS resolver and a `ts.net` split-DNS route take precedence. Restarting Tailscale did not help. Workaround: a hosts-file entry on that PC mapping the full tailnet name to the NAS's Tailscale IP (added by the owner). Root cause not investigated further.
- **QNAP package updates** may reset the serve configuration. Check with `tailscale serve status` on the NAS and rerun the command above if needed.
- **Turn it off:** `tailscale serve --https=8443 off` on the NAS.

On 2026-10-28 the owner supplied a DNS-console screenshot with MagicDNS enabled and no extra `ts.net` split route visible. A direct Tailscale internal DNS query from home-services resolved the NAS name. The guest does not accept Tailscale DNS (`CorpDNS: false`), so its ordinary resolver result is not a test of Titan. Titan direct and normal Windows DNS tests are still pending; preserve its hosts-file workaround until verified.
