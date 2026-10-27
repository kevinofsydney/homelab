# Operator SSH access

On 2026-10-27 the operator approved administration from the Framework laptop and Titan desktop, both running Windows, for all homelab management targets. Both complete public keys were validated with `ssh-keygen -lf` and added to the existing Proxmox root authorized-key file and the development VM's `devops` account. Only public keys were supplied; private keys remain on their originating Windows machines. Labels are `FRAMEWORK` and `TITAN`.

Actual device addresses and approved public keys are stored in ignored `config/site.json` and `ansible/inventory/hosts.yml`. Router reservation screenshots identify devices, but an IP reservation is not an SSH credential or a firewall allow rule. No router/firewall settings were changed. Ordinary key-based SSH remains in use; Tailscale enrollment is a separate pending step.

## Reusable guest access

Set `operator_ssh_public_keys` in ignored inventory to the approved full OpenSSH public-key lines. The default is an empty list. `operator-access.yml` provides a separate check/apply entry point; the development playbook also includes the role for future guests. The role validates the administrator name, checks key format and uses OpenSSH to parse each key before updating the existing file. It adds or relabels only matching approved entries and preserves all unrelated keys. It requires the guest administrator's existing cloud-init authorized-key file, and does not create accounts, grant coding workers SSH access, enable passwords or permit guest root login.

```sh
ANSIBLE_CONFIG=ansible/ansible.cfg .local/venv/bin/ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/operator-access.yml --check --diff
# Apply only approved key changes:
ANSIBLE_CONFIG=ansible/ansible.cfg .local/venv/bin/ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/operator-access.yml
```

Future application VM playbooks must explicitly include this role and its approved operator inventory; adding it to the development playbook does not automatically configure unrelated guests. Do not place operator private keys or management credentials inside a worker.

## Proxmox bootstrap access

Proxmox's `/root/.ssh/authorized_keys` was inspected and resolves to `/etc/pve/priv/authorized_keys`. This is a cluster-shared management file. It was updated by appending only missing approved public keys through the existing symlink; it was not atomically replaced, truncated, chmodded or recreated. Both prior entries remained byte-for-byte intact. Do not use the guest role against this root file or replace the symlink with a regular file. Review cluster scope before applying this process to a multi-node installation.

Proxmox root access is for the trusted human operator. Coding workers and assistant accounts do not receive any of these private keys or management routes. Adding SSH keys does not create Proxmox web-UI accounts or change PAM passwords.

## Windows verification

In PowerShell on each operator machine, connect as `root` to the actual Proxmox management address, or as `devops` to the observed guest address. Use `ssh -i "$env:USERPROFILE\.ssh\<private-key-filename>" <user>@<verified-address>` if the private key has a non-default filename. Addresses are in the private site inventory; confirm DHCP leases if they change. The private-key passphrase prompt, if configured, is the local key's passphrase, not the guest account password.

Before accepting a first-connection host-key prompt, compare against a fingerprint obtained through the trusted console or existing verified management session. The server's host key and the operator's public key are different identities. Do not suppress host-key checking or accept changed host keys without investigation. After connecting, check `hostname` and `whoami`, then exit before testing the next target. Report success for each machine/target pair.

Server-side evidence: both approved fingerprints were present on both targets; the guest key file remained mode 0600 and owned by `devops`; the Proxmox symlink and existing entries were preserved; the existing operator key still authenticated and guest sudo worked. A second Ansible check reported no changes. Client-side login from Framework/Titan remains unverified until the operator tests it; no private key was available to the deploying agent.

Validation commands: `python -m unittest discover -s tests -q` (17 passing tests), `python scripts/validate_repo.py` (24 JSON/YAML files), `ansible-playbook --syntax-check` for all five playbooks, and `git diff --check` passed. Final live operator-access check returned `ok=4 changed=0 failed=0` with no skipped tasks, including OpenSSH parsing of each public key.
