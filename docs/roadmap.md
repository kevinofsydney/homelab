# Later service work

The first milestone is deliberately small enough to verify on the 32 GB / 512 GB host. Each later stack gets its own pinned image set, backup/restore test, mount gate, private bind address and resource budget before being activated.

| Service | Planned data placement | Next release gate |
| --- | --- | --- |
| Paperless-ngx | PostgreSQL/index on SSD; media on dedicated QNAP export | Stack staged in `compose/paperless/`; test NFS, backup and restore |
| Immich | PostgreSQL/cache on SSD; originals on dedicated QNAP export | Use current upstream Compose as baseline, verify hardware transcoding and upload/backup behavior |
| n8n | DB/config on SSD; private editor | Staged in the separate application VM; Docker firewall activation awaits approval, followed by owner setup, isolation and recovery review |
| Audiobookshelf | Media read-only on QNAP; metadata/config on SSD | Verify ownership, library scan and backup |
| Ebook server | Books read-only on QNAP; config on SSD | Choose Kavita or alternative after current release review |
| Uptime Kuma | Config on SSD; private UI | Telegram alert credentials scoped to notifications |
| Hermes/Telegram | Isolated assistant with narrow tools | Verify maintenance status, identity verification and prompt injection handling |
| Public web app app | Separate app/database; hosting undecided | Confirm the accounting system product, export schema and billing rules; complete security review |

Paperless-AI, Grok integration and Pi-hole remain optional. NextDNS, Plex and BinaryLane stay untouched. Do not deploy every service into the development VM just because resources appear free at idle.
