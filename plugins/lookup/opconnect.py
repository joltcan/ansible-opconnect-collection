#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Fredrik Lundhag <f@mekk.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
    lookup: opconnect
    author: Fredrik Lundhag (@joltcan)
    version_added: "1.0" # for collections, use the collection version, not the Ansible version
    short_description: retreive information from vault(s) in 1Password via 1Password connect
    description: |
        Retreive information from vaults in 1Password via 1Password Connect (opconnect). An opconnect instance is needed,
        see https://github.com/1Password/connect
    options:
      _terms:
        description: Vault item too look for
        required: True
      vault:
        description: Name of the vault that the item resides in.
        required: True
      section:
        description: Item section, can be used with field below.
        required: False
      field:
        description: field to search for. Needed when section is used
        required: False
      op_connect_host:
        description: REST API endpoint for 1Password Connect
        env:
          - name: OP_CONNECT_HOST
        ini:
          - section: op_connect
            key: op_connect_host
        required: True
        type: string
      op_connect_token:
        description: API token for 1Password Connect access
        env:
          - name: OP_CONNECT_TOKEN
        ini:
          - section: op_connect
            key: op_connect_token
        required: True
        type: string
      op_connect_skip_verify:
        description: Skip TLS host verification
        env:
          - name: OP_CONNECT_SKIP_VERIFY
        ini:
          - section: op_connect
            key: op_connect_skip_verify
        type: boolean
        required: False
      op_connect_ca_bundle:
        description: Custom CA bundle for self signed certificates
        env:
          - name: OP_CONNECT_CA_BUNDLE
        ini:
          - section: op_connect
            key: op_connect_ca_bundle
        required: False
        type: boolean
"""

EXAMPLES = """
---
- hosts: 127.0.0.1
  tasks:
    - set_fact: foo_password="{{ lookup('opconnect', 'item', vault='OPS', section='creds', field='api_key') }}"
    - debug: msg="var is {{ foo_password }} "
    - debug: msg="{{ lookup('opconnect', 'item', vault='OPS') }}" # will return the password value of the item.

# Generic lookup
{{ lookup('opconnect', 'item', vault='OPS', section='creds', field='api_key') }} # foobar

"""

RETURN = """
  _list:
    description: 1Password item value
"""

import json
import requests

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        # First of all populate options,
        # this will already take into account env vars and ini config
        self.set_options(var_options=variables, direct=kwargs)

        display.vvvv(u"1Password Connect lookup initial terms is %s" % (terms))
        # populate our options
        server = self.get_option('op_connect_host')
        token = self.get_option('op_connect_token')
        skipverify = self.get_option('op_connect_skip_verify')
        cabundle = self.get_option('op_connect_ca_bundle')

        # verify that we have a proper token, and get a list of vaults since we need them
        # in the next step anyway
        try:
            vaults = self._get_vaults(server, token, cabundle, skipverify)
        except Exception as e:
            raise AnsibleError('ERROR: "%s": exception: %s' % (server, to_native(e)))

        # find the vault we need
        for _vault in vaults:
            if _vault['name'].lower() == self.get_option('vault').lower():
                vaultuuid = _vault['id']
        if not vaultuuid:
            raise AnsibleError('ERROR: Vault uuid not found')

        # convert or options to vars
        itemname = terms[0]
        field  = self.get_option('field')
        section = self.get_option('section')

        if section is not None:
            display.vvvv:(u"Using section: %s" % (section))

        display.vvvv(u"opconnect lookup using item %s, vault uuid: %s" % (itemname, vaultuuid))
        
        result = []
        # get our item/value
        try:
            item = self._get_item(server, token, itemname, vaultuuid, section, field, cabundle, skipverify)
            result.append(item.rstrip())
        except Exception as e:
            raise AnsibleError('ERROR: lookup of the value failed, could not be found. Maybe try and specify section or field?
                                Exception: %s' % to_native(e))

        return result

    def _get_item(self, server, token, itemname, vaultuuid, section, field, cabundle, skipverify):
        # https://support.1password.com/connect-api-reference/#list-items
        itemuuid = False
        headers = {'Authorization': 'Bearer ' + token,
                   'Content-type': 'application/json'}

        # TODO: Get payload filter to work
        # params = {'filter' : 'title eq "' + itemname + '"'}
        # https://support.1password.com/connect-api-reference/#list-items
        params = {}
        url = server + '/v1/vaults/' + vaultuuid + '/items'
        try:
            if skipverify is not None:
                response = requests.get(url, headers=headers, params=params, verify=False)
            elif cabundle is not None:
                response = requests.get(url, headers=headers, params=params, verify=cabundle)
            else:
                response = requests.get(url, headers=headers)
        except Exception as e:
            raise AnsibleError('ERROR: Can not reach "%s": error: %s' % (server, to_native(e)))
            
        data = json.loads(response.content)
        if not response.ok:
            raise AnsibleError('Failed to communicate with opconnect: %s' % data['message'])

        # iterate and find the item uuid
        for _item in data:
            if _item['title'].lower() == itemname.lower():
                itemuuid = _item['id']
        if not itemuuid:
            raise AnsibleError('Couldn\'t find the uuid for %s in 1Password connect' % itemname)

        display.vvvv('Section: %s, uuid: %s' % (section, itemuuid))

        # now get the entry with the vaultuiid and itemuuid
        # GET /v1/vaults/{vaultUUID}/items/{itemUUID}
        url = server + '/v1/vaults/' + vaultuuid + '/items/' + itemuuid
        try:
            if skipverify is not None:
                response = requests.get(url, headers=headers, verify=False)
            elif cabundle is not None:
                response = requests.get(url, headers=headers, verify=cabundle)
            else:
                response = requests.get(url, headers=headers)
        except Exception as e:
            raise AnsibleError('ERROR: Can not reach "%s": error: %s' % (server, to_native(e)))

        data = json.loads(response.content)
        if not response.ok:
            raise AnsibleError('Failed to communicate with opconnect: %s' % data['message'])

        # iterate and find the item uuid
        itemvalue = False
        sectionid = False

        for item in data['fields']:
            if section is not None and "section" in item:
                if item['section']['label'] == section and item['label'] == field:
                    itemvalue = item['value']
            else:
                # ignore section if we aren't looking for it
                if "section" in item:
                    continue

                # try to get a field without section
                if field is not None:
                    if item['label'] == field:
                        itemvalue = item['value']

                # if no field or section, just get the password by default
                # as the onepassword plugin does
                else:
                    if item['id'] == "password" and item['label'] == "password":
                        itemvalue = item['value']

        return(itemvalue)

    def _get_vaults(self, server, token, cabundle, skipverify):
        # https://support.1password.com/connect-api-reference/#list-vaults
        # GET /v1/vaults
        headers = {'Authorization': 'Bearer ' + token,
                   'Content-type': 'application/json'}

        try:
            if skipverify is not None:
                response = requests.get(server + '/v1/vaults', headers=headers, verify=False)
            elif cabundle is not None:
                response = requests.get(server + '/v1/vaults', headers=headers, verify=cabundle)
            else:
                response is not requests.get(server + '/v1/vaults', headers=headers)
        except Exception as e:
            raise AnsibleError('ERROR: Can not reach "%s": error: %s' % (server, to_native(e)))

        vaults = json.loads(response.content)
        if not response.ok:
            raise AnsibleError('ERROR: %s' % vaults['message'])

        return vaults
