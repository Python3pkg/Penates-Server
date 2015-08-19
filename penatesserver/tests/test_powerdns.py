# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from penatesserver.powerdns.models import Domain, Record


class TestLocalResolve(TestCase):
    ip = '192.168.1.1'
    domain_name = 'test.domain.org'

    @classmethod
    def setUpClass(cls):
        TestCase.setUpClass()
        cls.domain = Domain.objects.get_or_create(name=cls.domain_name)[0]
        d = cls.domain.name

        # ok
        Record(domain=cls.domain, type='A', content=cls.ip, name='a.%s' % d).save()
        Record(domain=cls.domain, type='CNAME', content='a.%s' % d, name='b.%s' % d).save()
        Record(domain=cls.domain, type='CNAME', content='b.%s' % d, name='c.%s' % d).save()
        Record(domain=cls.domain, type='CNAME', content='c.%s' % d, name='d.%s' % d).save()
        Record(domain=cls.domain, type='CNAME', content='d.%s' % d, name='e.%s' % d).save()

        # loop
        Record(domain=cls.domain, type='CNAME', content='g.%s' % d, name='f.%s' % d).save()
        Record(domain=cls.domain, type='CNAME', content='h.%s' % d, name='g.%s' % d).save()
        Record(domain=cls.domain, type='CNAME', content='f.%s' % d, name='h.%s' % d).save()

        # no answer
        Record(domain=cls.domain, type='CNAME', content='j.%s' % d, name='i.%s' % d).save()

    def test_ip(self):
        self.assertEqual(self.ip, Record.local_resolve(self.ip))

    def test_direct(self):
        self.assertEqual(self.ip, Record.local_resolve('a.%s' % self.domain_name))

    def test_indirect_1(self):
        self.assertEqual(self.ip, Record.local_resolve('b.%s' % self.domain_name))

    def test_indirect_2(self):
        self.assertEqual(self.ip, Record.local_resolve('c.%s' % self.domain_name))

    def test_indirect_3(self):
        self.assertEqual(self.ip, Record.local_resolve('d.%s' % self.domain_name))

    def test_indirect_4(self):
        self.assertEqual(self.ip, Record.local_resolve('e.%s' % self.domain_name))

    def test_loop(self):
        self.assertIsNone(Record.local_resolve('f.%s' % self.domain_name))
        self.assertIsNone(Record.local_resolve('g.%s' % self.domain_name))
        self.assertIsNone(Record.local_resolve('h.%s' % self.domain_name))

    def test_no_answer(self):
        self.assertIsNone(Record.local_resolve('i.%s' % self.domain_name))
