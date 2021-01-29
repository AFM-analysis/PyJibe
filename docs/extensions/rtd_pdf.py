from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from sphinx.util.nodes import nested_parse_with_titles

import os


class RTDPDF(Directive):
    def run(self):
        if "READTHEDOCS" in os.environ:
            project = os.environ["READTHEDOCS_PROJECT"]
            version = os.environ["READTHEDOCS_VERSION"]
            is_rtd = os.environ["READTHEDOCS"] == "True"
            link = "https://readthedocs.org/projects/" \
                   + "{}/downloads/pdf/{}/".format(project, version)
        else:
            is_rtd = False

        rst = []

        if is_rtd:
            rst = "This documentation is also available as a " \
                  + "`PDF <{}>`_.".format(link)
            rst = [rst]

        vl = ViewList(rst, "fakefile.rst")
        # Create a node.
        node = nodes.section()
        node.document = self.state.document
        # Parse the rst.
        nested_parse_with_titles(self.state, vl, node)
        return node.children


def setup(app):
    app.add_directive("rtd_pdf", RTDPDF)
