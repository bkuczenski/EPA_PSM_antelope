
from .kw_dict import mk_kwd


class PsmTerminationBuilder(object):
    """
    A tool to build container fragments for product system models, themselves modeled as fragments.

    Uses data in a "terminations" XLS sheet to map flows to terminations based on properties of the flow.  The flow
    properties are used as key headers in the kw_dict; the origins
    """
    def __init__(self, cat, fg, term_info, sheet='terminations'):
        self.cat = cat
        self.fg = fg
        self.term_dict = mk_kwd(term_info, sheet, kwcols=2, lower=False)

    def _get_term_dict(self, flow):
        key = tuple((flow.get(k) or '').strip() for k in self.term_dict[None])
        return self.term_dict[key]

    def terminate_child_flows(self, frag, *origins):
        for _f in frag.child_flows:

            _td = self._get_term_dict(_f.flow)

            for k in origins:
                try:
                    proc = self.cat.query(k).get(_td[k])
                except KeyError:
                    print('origin: %s | unable to retrieve %s (%s)' % (k, _td[k],
                                                                           _f.flow.link))
                    continue
                rx = proc.reference()
                _f.terminate(proc, scenario=k, term_flow=rx.flow)

    def build_container(self, psm, *origins, descend=True):
        container = self.fg.new_fragment(psm.flow, 'Output', Comment='Container for %s' % psm.name)
        self.fg.name_fragment(container, '%s Container' % psm.flow.name)
        container.terminate(psm, descend=descend)

        # should be an interface for this- child flows
        for c in psm.inventory():
            if c.is_reference:
                continue
            # if container_frag.has_child(c.flow, c.direction):
            #    continue
            _f = self.fg.new_fragment(c.flow, c.direction, parent=container)
            _f.set_background()

        self.terminate_child_flows(container, *origins)

        return container
