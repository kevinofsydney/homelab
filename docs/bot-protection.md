# AI crawler and botnet protection

This is a required design and acceptance policy for future public ingress. It describes controls to prepare and test; it does not claim that Cloudflare, router/firewall rules or application limits have already been deployed. Private services remain private throughout the initial milestone.

## Threat model

Protect confidentiality, account access and availability. Compliant crawlers may respect published preferences, while hostile scrapers and botnets can disguise user-agent strings, rotate addresses and keep sending requests after an application is stopped. Identify abuse from request behavior and telemetry; a user-agent alone does not prove the traffic is an AI crawler.

Filtering only on the Dell still consumes home bandwidth and host resources. Public HTTP traffic should be filtered upstream. No application filter guarantees protection of the home Internet connection if an attacker independently targets its public IP; prefer managed hosting when a public app becomes critical.

## Required service boundaries

| Services | Required access boundary |
| --- | --- |
| Proxmox, QNAP administration, SSH and agent administration | Trusted operator devices, Tailscale where applicable and independently tested LAN/firewall restrictions |
| Immich, Paperless, n8n editor and household media apps | Private Tailscale access, no public ingress |
| A future public web app | Deliberately published HTTPS origin with user authentication and upstream/application abuse controls |

Before publishing, inspect router forwarding, automatic UPnP mappings and IPv6 inbound reachability. Tailscale policy alone does not close alternate LAN or public paths. Keep databases and management interfaces outside the public route.

## Public web app controls

1. **Authenticate at the edge.** Where the app has no anonymous content requirement, prefer Cloudflare Access, or an equivalent identity gateway, restricted to approved users before requests reach the application. Keep application authentication, object/role authorization and admin MFA. Record identity-provider, account lifecycle and session-revocation decisions; a gateway is not user/admin authorization inside the app.
2. **Prevent origin bypass.** If hosted on the Dell, publish only the intended app through Cloudflare Tunnel, with no direct public route to the origin. A tunnel alone does not authenticate visitors. Enforce the selected Access policy at the connector/origin as supported, and reject unknown hostnames/routes. Document TLS termination and third-party handling of user data. Reassess the equivalent controls if production is hosted elsewhere.
3. **Filter unwanted traffic upstream.** Enable appropriate WAF protections and AI crawler blocking, then verify rule ordering and exceptions. Check current plan capabilities before relying on a feature. Cloudflare currently documents user-agent-based AI Crawl Control detection on its free plan, so crawler blocking cannot be the sole defense against disguised clients.
4. **Limit workload at the application.** Protect login, recovery and verification endpoints using both account/identity and IP signals. Rate-limit exports, uploads, searches and other expensive operations; bound request size, execution time, concurrency, database work and queues. Include aggregate capacity limits because distributed attacks can evade individual IP limits. Set and load-test actual thresholds against expected use; avoid blanket limits that lock out users sharing workplace or mobile addresses.
5. **Keep content private.** Require authorization for every record, document and export. Prevent public CDN caching of authenticated or user-specific responses. Serve a simple `robots.txt` requesting no crawling and use indexing restrictions where suitable. These communicate preferences and do not replace authentication or access controls.
6. **Observe and contain abuse.** Monitor request volume, authentication failures, latency, CPU/memory, database load and queue growth. Retain enough sanitized logs to diagnose incidents, excluding credentials, session tokens and user payloads. Prepare an operator-controlled emergency policy that restricts ingress to approved identities or disables the public route.

Turnstile may supplement exposed forms when justified. If added, validate each token on the server before processing the action; the browser widget alone is insufficient. Avoid blanket browser challenges on authenticated APIs, native clients or webhooks. Any exception needs explicit authentication and its own rate/resource limits.

## Optional defenses

Anubis, CrowdSec, Fail2ban and IP/ASN blocklists are optional additions after observing a concrete need. Do not make them initial prerequisites or treat them as complete protection against distributed traffic. If IP-based banning is added behind a proxy, accept visitor-IP headers only from trusted proxies and ensure bans target the actual client rather than the tunnel/proxy.

## Acceptance before public launch

- Anonymous and unapproved identities are denied before reaching user data or costly application work; user and admin permissions remain enforced after login.
- Direct-origin access fails over both IPv4 and IPv6; unknown hostnames/routes cannot reach management or private services.
- Tests cover repeated login failures, account attempts from changing IPs, shared user IPs, expensive operations and aggregate load. Legitimate use remains functional.
- Spoofed forwarding headers do not bypass identity or rate limits. Machine clients and any authorized webhook exceptions have explicit scoped authentication.
- Authenticated pages/exports are not publicly cached; compliant crawlers receive the intended policy, and noncompliant clients remain constrained by the other controls.
- Alerts and emergency ingress restrictions are exercised. Record actual settings, plan capabilities, test evidence, limitations and recovery steps in the service runbook without secrets.

Applying network, ingress, credential or running-service changes requires explicit operator approval under `AGENTS.md`. Passing source CI does not satisfy these live acceptance tests.

## Sources

Reviewed 2026-10-27. Recheck provider features before implementation.

- [Reported crawler load in the selfhosted discussion](https://www.reddit.com/r/selfhosted/comments/1xgae5q/so_tired_of_these_ai_crawlers/) is motivation, not verified attribution or deployment guidance.
- [Cloudflare Access application types](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/choose-application-type/) and [Tunnel routing](https://developers.cloudflare.com/tunnel/concepts/routing/).
- [AI Crawl Control detection and plan limits](https://developers.cloudflare.com/ai-crawl-control/get-started/) and [interaction with WAF rules](https://developers.cloudflare.com/ai-crawl-control/configuration/ai-crawl-control-with-waf/).
- [Rate-limiting guidance](https://developers.cloudflare.com/waf/rate-limiting-rules/best-practices/) and [mandatory Turnstile server validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/).
- [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) explains that robots.txt does not provide access authorization.
- [CrowdSec proxy/IP troubleshooting](https://docs.crowdsec.net/u/troubleshooting/security_engine/) describes correct visitor-IP handling behind proxies.
