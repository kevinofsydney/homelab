# Reusable private application pattern

Paperless is the prepared reference implementation. Immich, n8n and media stacks remain planned until their release-specific upstream configurations and site inputs are reviewed. This contract applies to each new stack; it does not activate a service.

For each `compose/<service>/` directory, provide `compose.yml`, `.env.example` with placeholders, and a runbook covering requirements, data mapping, startup checks, health, backup, isolated restore, upgrade and rollback. Put actual addresses, immutable reviewed images and secrets in ignored configuration; restrict secret-file permissions. Never commit the generated file.

| Concern | Required pattern |
| --- | --- |
| Resource budget | Record measured/estimated RAM, CPU, disk growth and processing peaks; review aggregate host capacity |
| Data placement | Database, cache and metadata on Dell SSD; bulk originals/media on a dedicated verified QNAP export |
| Mount gate | Validate exact source/filesystem/mountpoint before start and backup; fail closed on missing NAS; bind mounts use `create_host_path: false` |
| Startup | Plan/Compose validation by default; explicit apply only after approval; no automatic app restart that bypasses mount checks |
| Network | Private Tailscale bind with tested access policy; databases internal; public webhooks require separate ingress review |
| Identity | Verify numeric ownership for each image; no privileged container or host Docker socket without separate justified review |
| Release selection | Begin from official upstream Compose for a reviewed release; pin compatible image digests together; preserve upstream health/dependency checks |
| Recovery | Consistent DB dump plus file/config/secret recovery procedure; verified separate backup destination; isolated restore before production |
| Upgrade | Back up, record current digests, review migrations, apply approved change and check health; migrations may require restoring DB and files to roll back |

Paperless uses PostgreSQL, broker and document paths as documented in its runbook. Immich needs a compatible upstream database/extension and application image set, original-photo backup and a separately reviewed acceleration setup. n8n needs a backed-up encryption key as well as DB/config, private editor access and a deliberate webhook decision. Media servers should mount existing libraries read-only by default and keep metadata on SSD; preserve QNAP Plex. Select the actual media applications before preparing their release-specific stacks.

Acceptance includes trusted access, rejected unauthorized access, DB persistence, exact NAS identity, NAS-unavailable startup refusal, backup failure on a missing destination, and successful isolated restore. Record versions and dated evidence in shared documentation without secrets or private inventory.
