# Ubuntu template, performed on the Proxmox host

Use a verified Ubuntu Server 24.04 LTS cloud image from the [Ubuntu cloud images](https://cloud-images.ubuntu.com/noble/current/). Record and verify its published SHA256 before import. Confirm the Proxmox storage ID, bridge, template VMID and available disk space in `config/site.json`. The commands below are a reviewed operator procedure because they create a VM and change host state.

```sh
qm create 9000 --name ubuntu-2404-cloud-template --memory 2048 --cores 2 --net0 virtio,bridge=<BRIDGE>
qm importdisk 9000 noble-server-cloudimg-amd64.img <STORAGE_ID>
qm set 9000 --scsihw virtio-scsi-single --scsi0 <STORAGE_ID>:vm-9000-disk-0
qm set 9000 --ide2 <STORAGE_ID>:cloudinit --boot order=scsi0 --serial0 socket --vga serial0
qm set 9000 --agent enabled=1
qm template 9000
```

Replace all placeholders. Confirm the imported disk volume name with `pvesm list <STORAGE_ID>` before the `scsi0` command; storage backends may assign a different name. The image contains cloud-init; the VM provisioner supplies the login user and SSH public key. No password is configured. Cloud-init custom snippets are deliberately unnecessary for the first milestone; `proxmox/cloud-init/user-data.example.yaml` documents the intended guest policy if a custom snippet is later needed.

The provisioner clones this template, enlarges the disk if needed, sets CPU/RAM/network/cloud-init and starts the VM. It refuses to alter an existing VM. If an interrupted run leaves VMID 100, inspect it in Proxmox and either complete it manually or remove it after explicit review before rerunning.
