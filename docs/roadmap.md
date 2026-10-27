# Later service work

The first milestone is deliberately small enough to verify on the 32 GB / 512 GB host. Each later stack gets its own pinned image set, backup/restore test, mount gate, private bind address and resource budget before being activated.

| Service | Planned data placement | Next release gate |
| --- | --- | --- |
| Paperless-ngx | PostgreSQL/index on SSD; media on dedicated QNAP export | Running privately; synthetic OCR and guest-reboot startup tested; NAS-loss behavior remains untested |
| Immich | PostgreSQL/cache on SSD; originals on dedicated QNAP export | Use current upstream Compose as baseline, verify hardware transcoding and upload/backup behavior |
| n8n | Existing cloud service | Self-hosting is out of scope until the operator requests it; staged files are inactive |
| Audiobookshelf | Media read-only on QNAP; metadata/config on SSD | Verify ownership, library scan and backup |
| Ebook server | Books read-only on QNAP; config on SSD | Choose Kavita or alternative after current release review |
| Uptime Kuma | SQLite data on SSD; private UI | Running with one Paperless monitor; guest-reboot recovery and notification setup remain unverified |
| Hermes/Telegram | Isolated assistant with narrow tools; own guest proposed | Rebuild from [handoff](../agents/handoffs/ufc-hermes-rebuild.md); verify identity allowlist, sandbox egress and prompt injection handling |
| UFC agent | Small guest: read-only n8n gateway and owner-only Telegram bot | Re-implement from the handoff specification with boundary tests first |
| Public web app app | Separate app/database; hosting undecided | Confirm the accounting system product, export schema and billing rules; complete security review |

Paperless-AI, Grok integration and Pi-hole remain optional. NextDNS, Plex and any remaining BinaryLane resources stay untouched. Do not deploy every service into the development VM just because resources appear free at idle.
