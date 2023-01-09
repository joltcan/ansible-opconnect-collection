# 1Password Connect Ansible Collection

This 1Password Connect collection contains a lookup module that can easily get the password or other field value into your ansible code.

You can learn more about [Secrets Automation and 1Password Connect](https://1password.com/secrets/) on 1Password website.

## Table of Contents

* [Requirements](#requirements)
* [Installation](#installation)
* [Module & Environment Variables](#module-variables)
* [About 1Password](#about-1password)

### Requirements
- Python >= 3.6.0
- 1Password Connect >= 1.0.0
    
#### Supported Ansible Versions

This collection has been tested against the following Ansible versions:
* `ansible-core`: >=2.9, 2.11, 2.12
* `ansible`: >=4.0, <5.0

## Installation

You can install the Ansible collection from [Ansible Galaxy](https://galaxy.ansible.com/joltcan/op):

```
ansible-galaxy collection install joltcan.op
```

## Plugin Variables

The plugin support the following variable definitions. You may either explicitly define the value on the task or let Ansible fallback to an environment variable to use the same value across all tasks.

Environment variables are ignored if the module variable is defined for a task.

| Plugin Variable | Environment Variable | Description                                                                           |
|----------------:|----------------------|---------------------------------------------------------------------------------------|
|        `op_connect_host_api` | `OP_CONNECT_HOST_API`         | URL of a 1Password Connect API Server                                   |
|       `op_connect_token_api` | `OP_CONNECT_TOKEN_API`        | JWT used to authenticate 1Password Connect API requests                 |
|   `op_connect_ca_bundle_api` | `OP_CONNECT_CA_BUNDLE_API`    | (Optional) Use CA bundle file for self-signed server certificate        |
| `op_connect_skip_verify_api` | `OP_CONNECT_SKIP_VERIFY_API` | (Optional) Skip certificate verification                                |


## `joltcan.op.connect` plugin


### Example Usage
**Get Item**
```yaml
---
- name: Lookup a password
  hosts: localhost
  environment:
    OP_CONNECT_HOST_API: http://localhost:8001
    OP_CONNECT_TOKEN_API: "api.jwt.here"
  collections:
    - joltcan.op.connect
  tasks:
    - set_fact: foo_password="{{ lookup('joltcan.op.op_lookup', 'item', vault='OPS', section='creds', field='api_key') }}"
    - debug: msg="var is {{ foo_password }} "
    - debug: msg="{{ lookup('joltcan.op.op_lookup', 'item', vault='OPS') }}" # will return the password value of the item.

```
<details>
<summary>View output registered to the `joltcan.op.op_lookup`</summary>
<br>

```
ok: [localhost] => {
    msg: "var is apikey"
}
ok: [localhost] => {
    msg: "somepassword"
}

```
</details>

**Update an Item**

**❗️Note❗** There is currently no functionality to update vault items. If you wish, use the offical [onepassword.connect](https://github.com/1Password/ansible-onepasswordconnect-collection) collection for this.

## About 1Password

[**1Password**](https://1password.com) is a privacy-focused password manager that keeps you safe online.