"""
Functions and utilities for generating random mass and price data for inventory entries
"""

import random
import os
import json

from .kw_dict import mk_kwd


class MockCfGenerator(object):
    """
    This class generates random mass and price values based on a collection of multiplicative keyword "hints" curated
    by the user.
    """

    m_base = -3
    p_base = -3
    sig_base = 0.65

    def __init__(self, mass_qty, price_qty, hint_file, sheet='mass_hints', save_file='cfs.json'):
        self.mass = mass_qty
        self.price = price_qty
        self.kwd = mk_kwd(hint_file, sheet=sheet)
        self.save_file = save_file
        if os.path.exists(self.save_file):
            with open(self.save_file) as fp:
                self._cf_dict = json.load(fp)
        else:
            self._cf_dict = {}

    def save(self):
        with open(self.save_file, 'w') as fp:
            json.dump(self._cf_dict, fp)
        print('Wrote CFs to %s' % self.save_file)

    def mock_cfs(self, flow, demo=True):
        m = p = 1.0
        sig = self.sig_base
        for k in ('PartType', 'Material', 'Size'):
            if flow.has_property(k):
                kw = flow[k].lower()
                if kw in self.kwd:
                    val_d = self.kwd[kw]
                    m *= val_d['mass']
                    p *= val_d['price']
                    if demo:
                        print('kw %s = %s --> %r' % (k, kw, val_d))
                    sig *= 0.75  # narrow sigma for each specification
                else:
                    if kw is not None:
                        print('missing kwd %s' % kw)
        m *= random.lognormvariate(self.m_base, sig)
        p *= random.lognormvariate(self.p_base, sig)
        if demo:
            print('[%s] %s: mass %3g %s; price: %3g %s' % (flow.external_ref, flow.name,
                                                           m, self.mass.unit(),
                                                           p, self.price.unit()))
        return m, p

    def characterize(self, flow, demo=False):
        if flow.link not in self._cf_dict:
            m = self.mass.cf(flow)
            p = self.price.cf(flow)
            if m == 0 and p == 0:
                m, p = self.mock_cfs(flow, demo=demo)
                flow.characterize(self.mass, m)
                flow.characterize(self.price, p)
            self._cf_dict[flow.link] = {'mass': m, 'price': p}
        self.check(flow, demo=demo)

    def check(self, f, demo=True):
        """
        This function is mainly to demonstrate that the characterization stuck
        :param f:
        :param demo:
        :return:
        """
        assert f.link in self._cf_dict
        m = self.mass.cf(f)
        p = self.price.cf(f)
        if demo:
            print('%s [%s]\nCFs: mass: %.3g %s; price: %.3g %s' % (f, f.external_ref,
                                                                   m, self.mass.unit(), p, self.price.unit()))
        assert m == self._cf_dict[f.link]['mass']
        assert p == self._cf_dict[f.link]['price']
