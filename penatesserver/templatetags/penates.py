# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import template
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
    return str(network.netmask)


@register.filter
def subnet_mask_len(subnet):
    """
    >>> subnet_mask_len('192.168.56.1/24')
    '24'
    """
    network = netaddr.IPNetwork(subnet)
    return str(network.prefixlen)


@register.filter
def subnet_address(subnet):
    """
    >>> subnet_address('192.168.56.1/24')
    '192.168.56.0'
    """
    network = netaddr.IPNetwork(subnet)
    return str(network.network)


@register.filter
def subnet_broadcast(subnet):
    """
    >>> subnet_broadcast('192.168.56.1/24')
    '192.168.56.255'
    """
    network = netaddr.IPNetwork(subnet)
    return str(network.broadcast)


@register.filter
def subnet_start(subnet):
    """
    >>> subnet_start('192.168.56.1/24')
    '192.168.56.32'
    """
    network = netaddr.IPNetwork(subnet)
    size = 32 if network.version == 4 else 128
    return str(network.network + 2 ** max(size - network.prefixlen - 3, 0))


@register.filter
def subnet_end(subnet):
    """
    >>> subnet_end('192.168.56.1/24')
    '192.168.56.254'
    """
    network = netaddr.IPNetwork(subnet)
    size = 32 if network.version == 4 else 128
    return str(network.network - 2 + 2 ** (size - network.prefixlen))
