
"""
Tests for the abc_backend module.
"""

import unittest
from .. import abc_backend as abcb
from .....protect import PROTECTION_PUBLIC, PROTECTION_PRIVATE


class NamespaceTemplateEntityTest(unittest.TestCase):
    """Test the NamespaceTemplateEntity class"""

    def test_getters__non_none(self) -> None:
        """Test the getters with non-none values.."""
        nte = abcb.NamespaceTemplateEntity('N1', PROTECTION_PUBLIC, 'x')
        self.assertEqual(abcb.ACTIVITY_TEMPLATE_DEFINITION, nte.activity)
        self.assertEqual('x', nte.purpose)
        self.assertEqual('N1', nte.namespace)
        self.assertEqual(PROTECTION_PUBLIC, nte.protection)
        self.assertFalse(nte.is_default_namespace())
        self.assertFalse(nte.is_default_protection())

    def test_getters__none(self) -> None:
        """Test the getters with none values."""
        nte = abcb.NamespaceTemplateEntity(None, None, 'y')
        self.assertEqual('y', nte.purpose)
        self.assertIsNone(nte.namespace)
        self.assertIsNone(nte.protection)
        self.assertTrue(nte.is_default_namespace())
        self.assertTrue(nte.is_default_protection())

    def test_eq_ne__non_none(self) -> None:
        """Test equals"""
        nte1 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PUBLIC, 'x')
        nte2 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PUBLIC, 'x')
        nte3 = abcb.NamespaceTemplateEntity('n1', PROTECTION_PUBLIC, 'x')
        nte4 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PUBLIC, 'y')
        nte5 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PRIVATE, 'x')
        nte6 = abcb.NamespaceTemplateEntity(None, None, 'z')
        self.assertFalse(nte1 == None)
        self.assertTrue(nte1 != None)
        self.assertFalse(nte1 == '')
        self.assertTrue(nte1 != '')
        self.assertTrue(nte1 == nte1)
        self.assertFalse(nte1 != nte1)
        self.assertTrue(nte1 == nte2)
        self.assertFalse(nte1 != nte2)
        self.assertFalse(nte1 == nte3)
        self.assertTrue(nte1 != nte3)
        self.assertFalse(nte1 == nte4)
        self.assertTrue(nte1 != nte4)
        self.assertFalse(nte1 == nte5)
        self.assertTrue(nte1 != nte5)
        self.assertFalse(nte1 == nte6)
        self.assertTrue(nte1 != nte6)

    def test_eq_ne__none(self) -> None:
        """Test equals"""
        nte1 = abcb.NamespaceTemplateEntity(None, None, 'z')
        nte2 = abcb.NamespaceTemplateEntity(None, None, 'z')
        nte3 = abcb.NamespaceTemplateEntity('n1', PROTECTION_PUBLIC, 'x')
        nte4 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PUBLIC, 'y')
        nte5 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PRIVATE, 'x')
        self.assertFalse(nte1 == None)
        self.assertTrue(nte1 != None)
        self.assertFalse(nte1 == '')
        self.assertTrue(nte1 != '')
        self.assertTrue(nte1 == nte1)
        self.assertFalse(nte1 != nte1)
        self.assertTrue(nte1 == nte2)
        self.assertFalse(nte1 != nte2)
        self.assertFalse(nte1 == nte3)
        self.assertTrue(nte1 != nte3)
        self.assertFalse(nte1 == nte4)
        self.assertTrue(nte1 != nte4)
        self.assertFalse(nte1 == nte5)
        self.assertTrue(nte1 != nte5)

    def test_hash(self) -> None:
        nte1 = abcb.NamespaceTemplateEntity(None, None, 'z')
        nte2 = abcb.NamespaceTemplateEntity(None, None, 'z')
        nte3 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PUBLIC, 'y')
        nte4 = abcb.NamespaceTemplateEntity('N1', PROTECTION_PRIVATE, 'x')
        self.assertEqual(hash(nte1), hash(nte1))
        self.assertEqual(hash(nte1), hash(nte2))
        self.assertEqual(hash(nte3), hash(nte3))
        self.assertNotEqual(hash(nte2), hash(nte3))
        self.assertNotEqual(hash(nte3), hash(nte4))


class GatewayConfigEntityTest(unittest.TestCase):
    """Test the GatewayConfigEntity class"""

    def test_getters(self) -> None:
        """Test the getters with non-none values.."""
        gcte = abcb.GatewayConfigEntity('N1', PROTECTION_PUBLIC, 'x')
        self.assertEqual(abcb.ACTIVITY_PROXY_CONFIGURATION, gcte.activity)
        self.assertEqual('x', gcte.purpose)
        self.assertEqual('N1', gcte.namespace_id)
        self.assertEqual(PROTECTION_PUBLIC, gcte.protection)

    def test_eq_ne(self) -> None:
        """Test equals"""
        gce1 = abcb.GatewayConfigEntity('N1', PROTECTION_PUBLIC, 'x')
        gce2 = abcb.GatewayConfigEntity('N1', PROTECTION_PUBLIC, 'x')
        gce3 = abcb.GatewayConfigEntity('n1', PROTECTION_PUBLIC, 'x')
        gce4 = abcb.GatewayConfigEntity('N1', PROTECTION_PUBLIC, 'y')
        gce5 = abcb.GatewayConfigEntity('N1', PROTECTION_PRIVATE, 'x')
        self.assertFalse(gce1 == None)
        self.assertTrue(gce1 != None)
        self.assertFalse(gce1 == '')
        self.assertTrue(gce1 != '')
        self.assertTrue(gce1 == gce1)
        self.assertFalse(gce1 != gce1)
        self.assertTrue(gce1 == gce2)
        self.assertFalse(gce1 != gce2)
        self.assertFalse(gce1 == gce3)
        self.assertTrue(gce1 != gce3)
        self.assertFalse(gce1 == gce4)
        self.assertTrue(gce1 != gce4)
        self.assertFalse(gce1 == gce5)
        self.assertTrue(gce1 != gce5)

    def test_hash(self) -> None:
        gce3 = abcb.GatewayConfigEntity('N1', PROTECTION_PUBLIC, 'y')
        gce4 = abcb.GatewayConfigEntity('N1', PROTECTION_PRIVATE, 'x')
        self.assertEqual(hash(gce3), hash(gce3))
        self.assertNotEqual(hash(gce3), hash(gce4))


class ServiceColorTemplateEntityTest(unittest.TestCase):
    """Test the ServiceColorTemplateEntity class"""

    def test_getters__non_none(self) -> None:
        """Test the getters with non-none values.."""
        scte = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'x')
        self.assertEqual(abcb.ACTIVITY_TEMPLATE_DEFINITION, scte.activity)
        self.assertEqual('x', scte.purpose)
        self.assertEqual('N1', scte.namespace)
        self.assertEqual('s1', scte.service)
        self.assertEqual('c1', scte.color)
        self.assertFalse(scte.is_default_namespace())
        self.assertFalse(scte.is_default_service())
        self.assertFalse(scte.is_default_color())

    def test_getters__none(self) -> None:
        """Test the getters with none values."""
        scte = abcb.ServiceColorTemplateEntity(None, None, None, 'y')
        self.assertEqual('y', scte.purpose)
        self.assertIsNone(scte.namespace)
        self.assertIsNone(scte.service)
        self.assertIsNone(scte.color)
        self.assertTrue(scte.is_default_namespace())
        self.assertTrue(scte.is_default_service())
        self.assertTrue(scte.is_default_color())

    def test_eq_ne__non_none(self) -> None:
        """Test equals"""
        scte1 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'x')
        scte2 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'x')
        scte3 = abcb.ServiceColorTemplateEntity('n1', 's1', 'c1', 'x')
        scte4 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'y')
        scte5 = abcb.ServiceColorTemplateEntity('N1', 's2', 'c1', 'x')
        scte6 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c2', 'x')
        scte7 = abcb.ServiceColorTemplateEntity(None, None, None, 'z')
        self.assertFalse(scte1 == None)
        self.assertTrue(scte1 != None)
        self.assertFalse(scte1 == '')
        self.assertTrue(scte1 != '')
        self.assertTrue(scte1 == scte1)
        self.assertFalse(scte1 != scte1)
        self.assertTrue(scte1 == scte2)
        self.assertFalse(scte1 != scte2)
        self.assertFalse(scte1 == scte3)
        self.assertTrue(scte1 != scte3)
        self.assertFalse(scte1 == scte4)
        self.assertTrue(scte1 != scte4)
        self.assertFalse(scte1 == scte5)
        self.assertTrue(scte1 != scte5)
        self.assertFalse(scte1 == scte6)
        self.assertTrue(scte1 != scte6)
        self.assertFalse(scte1 == scte7)
        self.assertTrue(scte1 != scte7)

    def test_eq_ne__none(self) -> None:
        """Test equals"""
        scte1 = abcb.ServiceColorTemplateEntity(None, None, None, 'z')
        scte2 = abcb.ServiceColorTemplateEntity(None, None, None, 'z')
        scte3 = abcb.ServiceColorTemplateEntity('n1', 's1', 'c1', 'x')
        scte4 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'y')
        scte5 = abcb.ServiceColorTemplateEntity('N1', 's2', 'c1', 'x')
        scte6 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c2', 'x')
        self.assertFalse(scte1 == None)
        self.assertTrue(scte1 != None)
        self.assertFalse(scte1 == '')
        self.assertTrue(scte1 != '')
        self.assertTrue(scte1 == scte1)
        self.assertFalse(scte1 != scte1)
        self.assertTrue(scte1 == scte2)
        self.assertFalse(scte1 != scte2)
        self.assertFalse(scte1 == scte3)
        self.assertTrue(scte1 != scte3)
        self.assertFalse(scte1 == scte4)
        self.assertTrue(scte1 != scte4)
        self.assertFalse(scte1 == scte5)
        self.assertTrue(scte1 != scte5)
        self.assertFalse(scte1 == scte6)
        self.assertTrue(scte1 != scte6)

    def test_hash(self) -> None:
        nte1 = abcb.ServiceColorTemplateEntity(None, None, None, 'z')
        nte2 = abcb.ServiceColorTemplateEntity(None, None, None, 'z')
        nte3 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'y')
        nte4 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c1', 'x')
        nte5 = abcb.ServiceColorTemplateEntity('N1', 's2', 'c1', 'x')
        nte6 = abcb.ServiceColorTemplateEntity('N1', 's1', 'c2', 'x')
        self.assertEqual(hash(nte1), hash(nte1))
        self.assertEqual(hash(nte1), hash(nte2))
        self.assertEqual(hash(nte3), hash(nte3))
        self.assertNotEqual(hash(nte2), hash(nte3))
        self.assertNotEqual(hash(nte3), hash(nte4))
        self.assertNotEqual(hash(nte4), hash(nte5))
        self.assertNotEqual(hash(nte5), hash(nte6))


class ServiceIdConfigEntityTest(unittest.TestCase):
    """Test the ServiceIdConfigEntity class"""

    def test_getters(self) -> None:
        """Test the getters with non-none values.."""
        sice = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'x')
        self.assertEqual(abcb.ACTIVITY_PROXY_CONFIGURATION, sice.activity)
        self.assertEqual('x', sice.purpose)
        self.assertEqual('N1', sice.namespace_id)
        self.assertEqual('si1', sice.service_id)
        self.assertEqual('s1', sice.service)
        self.assertEqual('c1', sice.color)

    def test_eq_ne(self) -> None:
        """Test equals"""
        sice1 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'x')
        sice2 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'x')
        sice3 = abcb.ServiceIdConfigEntity('n1', 'si1', 's1', 'c1', 'x')
        sice4 = abcb.ServiceIdConfigEntity('N1', 'si2', 's1', 'c1', 'x')
        sice5 = abcb.ServiceIdConfigEntity('N1', 'si1', 's2', 'c1', 'x')
        sice6 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c2', 'x')
        sice7 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'y')
        self.assertFalse(sice1 == None)
        self.assertTrue(sice1 != None)
        self.assertFalse(sice1 == '')
        self.assertTrue(sice1 != '')
        self.assertTrue(sice1 == sice1)
        self.assertFalse(sice1 != sice1)
        self.assertTrue(sice1 == sice2)
        self.assertFalse(sice1 != sice2)
        self.assertFalse(sice1 == sice3)
        self.assertTrue(sice1 != sice3)
        self.assertFalse(sice1 == sice4)
        self.assertTrue(sice1 != sice4)
        self.assertFalse(sice1 == sice5)
        self.assertTrue(sice1 != sice5)
        self.assertFalse(sice1 == sice6)
        self.assertTrue(sice1 != sice6)
        self.assertFalse(sice1 == sice7)
        self.assertTrue(sice1 != sice7)

    def test_hash(self) -> None:
        sice2 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'x')
        sice3 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'x')
        sice4 = abcb.ServiceIdConfigEntity('N2', 'si1', 's1', 'c1', 'x')
        sice5 = abcb.ServiceIdConfigEntity('N1', 'si2', 's1', 'c1', 'x')
        sice6 = abcb.ServiceIdConfigEntity('N1', 'si1', 's2', 'c1', 'x')
        sice7 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c2', 'x')
        sice8 = abcb.ServiceIdConfigEntity('N1', 'si1', 's1', 'c1', 'y')
        self.assertEqual(hash(sice2), hash(sice2))
        self.assertEqual(hash(sice2), hash(sice3))
        self.assertNotEqual(hash(sice3), hash(sice4))
        self.assertNotEqual(hash(sice4), hash(sice5))
        self.assertNotEqual(hash(sice5), hash(sice6))
        self.assertNotEqual(hash(sice6), hash(sice7))
        self.assertNotEqual(hash(sice7), hash(sice8))
