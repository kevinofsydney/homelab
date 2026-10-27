# Hermes VM isolation: proposed initial boundary

Status: **prepared for review, not deployed or tested**. The owner requested a Telegram-connected Hermes agent. VM 101 is running with Proxmox autostart enabled; as of 2026-10-28 no VM-specific policy is installed, the guest agent does not respond, and no assistant gateway or credentials are configured. Do not activate the agent before verifying isolation.

The review-only [example](../proxmox/firewall/hermes.fw.example) uses the existing development VM's IPv4 private-range restriction as a starting point: permit DHCP and the verified router's DNS, reject private, link-local and carrier-grade NAT destinations, and reject IPv6 egress. Inbound is unchanged so trusted operator SSH remains possible. Replace the router placeholder from ignored site inventory only after verification. Do not paste the example directly into Proxmox.

**This is an initial private-network boundary, not a destination allowlist.** Public IPv4 internet remains accessible, including arbitrary public services. DNS can be used for exfiltration, and compromised guest software can communicate through internet relays. This does not satisfy the stronger host-only egress objective in the [Hermes plan](hermes-n8n-telegram-plan.md); design and prove a separately enforced egress proxy or equivalent before claiming that objective. Do not join this guest to Tailscale without a separately reviewed tailnet policy.

## Before applying

1. Obtain explicit approval for the VM-specific firewall change. Verify the guest's IP and SSH host key through a trusted console path; resolve its nonresponsive guest agent. Confirm the actual DHCP/DNS dependencies and host firewall status. Confirm no existing `101.fw` will be overwritten and review the complete rendered policy, including IPv6 behavior and how to recover console access.
2. Back up existing state and arrange a timed, VM-101-only rollback. Do not disable the shared cluster firewall or alter VM 100 or 130 as a rollback. Apply only the reviewed VM policy using Proxmox-supported operations and verify compiled rules. Keep Proxmox console access available.
3. From the guest, as both the agent account and guest root, check TCP connections to Proxmox, QNAP, router administration and home-services are rejected; verify IPv6 and CGNAT paths and verify DNS, DHCP, package access and required public endpoints. Retest from the actual agent sandbox. Ensure operator SSH, Proxmox management, Paperless and Uptime Kuma remain accessible.
4. If verification fails, use the timed rollback or remove only the newly installed VM policy and verify access. Retain evidence and report that the guest is unisolated. If it passes, document the rules, tests and rollback; then separately review provider credentials, Telegram user restrictions, MCP authority and service supervision.
5. Test a guest reboot after installation and an owner-approved host reboot at an appropriate time. Verify firewall enforcement, VM autostart, service restart and a usable Telegram response. Configuration flags alone do not prove recovery.

The example is not a generic sandbox, a public endpoint allowlist, or proof that the setup is safe. Check rules against the running Proxmox version, router and actual VM networks before applying.
