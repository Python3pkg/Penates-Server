# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import base64
import uuid
from django import template
from django.utils.six import text_type
import netaddr

__author__ = 'Matthieu Gallet'
register = template.Library()


@register.filter
def subnet_mask(subnet):
    """
    >>> subnet_mask('192.168.56.1/24')
    '255.255.255.0'
    """
    network = netaddr.IPNetwork(subnet)
    return text_type(network.netmask)


@register.filter
def subnet_mask_len(subnet):
    """
    >>> subnet_mask_len('192.168.56.1/24')
    '24'
    """
    network = netaddr.IPNetwork(subnet)
    return text_type(network.prefixlen)


@register.filter
def subnet_address(subnet):
    """
    >>> subnet_address('192.168.56.1/24')
    '192.168.56.0'
    """
    network = netaddr.IPNetwork(subnet)
    return text_type(network.network)


@register.filter
def subnet_broadcast(subnet):
    """
    >>> subnet_broadcast('192.168.56.1/24')
    '192.168.56.255'
    """
    network = netaddr.IPNetwork(subnet)
    return text_type(network.broadcast)


@register.filter
def subnet_start(subnet):
    """
    >>> subnet_start('192.168.56.1/24')
    '192.168.56.32'
    """
    network = netaddr.IPNetwork(subnet)
    size = 32 if network.version == 4 else 128
    return text_type(network.network + 2 ** max(size - network.prefixlen - 3, 0))


@register.filter
def subnet_end(subnet):
    """
    >>> subnet_end('192.168.56.1/24')
    '192.168.56.254'
    """
    network = netaddr.IPNetwork(subnet)
    size = 32 if network.version == 4 else 128
    return text_type(network.network - 2 + 2 ** (size - network.prefixlen))


@register.simple_tag
def generate_uuid():
    return text_type(uuid.uuid4()).upper()


def base64_encode(binary_content):
    """
    >>> base64_encode('VW1JWWhQTlBPcXMwPQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tQWI0WGdCNTlpUGxkekRoeGUxNE51UHZ1eDZVCkNjUHdxbTNXaGFw')[0:50]
    'VlcxSldXaFFUbEJQY1hNd1BRb3RMUzB0TFVWT1JDQkRSVkpVU1'
    >>> ord(base64_encode('VW1JWWhQTlBPcXMwPQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tQWI0WGdCNTlpUGxkekRoeGUxNE51UHZ1eDZVCkNjUHdxbTNXaGFw')[50])
    10
    """
    if isinstance(binary_content, text_type):
        binary_content = binary_content.encode('utf-8')
    value = base64.b64encode(binary_content)
    return b'\n'.join([value[i:i+50] for i in range(0, len(value), 50)])


@register.filter
def base64_file(filename):
    with open(filename, 'rb') as fd:
        binary_content = fd.read()
    value = base64.b64encode(binary_content)
    return b'\n'.join([value[i:i+50] for i in range(0, len(value), 50)])
