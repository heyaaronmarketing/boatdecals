# -*- coding: utf-8 -*-
"""Inline worker/decode.js into the browser, from the one source.

The registration checker and the HIN decoder are needed in three places: the
order form, the two free tool pages, and the MCP server. Before this, the
registration logic existed only as a JavaScript string inside validate.py and
the HIN logic only inside tools.py - so putting them on the worker would have
created a second copy of each.

Instead worker/decode.js is the single implementation and this ships it to the
browser. The transform is mechanical and tiny: drop the `import` line, drop the
`export ` keywords, and supply the tables as a local. verify.py fails the build
if the inlined copy ever stops matching the source, so there is no way to patch
one and forget the other.

Proven before the switch: worker/decode.js and the validator it replaces agree
on level, corrected spacing and state across 490 inputs - every vessel prefix
in every shape, all nine postal-code confusions, and the malformed cases. The
only wording that changed was Maine's, where the old string was a hardcoded
duplicate of the note in content.py and the new one reads the real thing.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _strip_module(src, drop_import=True):
    out = []
    for line in src.splitlines():
        if drop_import and re.match(r"^\s*import\s", line):
            continue
        line = re.sub(r"^export\s+(const|function|let|var|class)\s", r"\1 ", line)
        out.append(line)
    return "\n".join(out)


def decode_js():
    """The shared module, as a browser IIFE exposing window.NMB_DECODE."""
    data = (ROOT / "worker" / "decode-data.js").read_text(encoding="utf-8")
    logic = (ROOT / "worker" / "decode.js").read_text(encoding="utf-8")

    # `export const T = {...}` becomes a local the stripped logic closes over.
    data = _strip_module(data, drop_import=False)
    data = re.sub(r"^const T = ", "var T = ", data, count=1, flags=re.M)

    return ("/* SHARED: worker/decode.js, inlined by engine/shared_js.py. "
            "One implementation - edit the worker file, not this. */\n"
            "(function(){\n" + data + "\n" + _strip_module(logic) + "\n"
            "window.NMB_DECODE={checkRegistration:checkRegistration,"
            "decodeHin:decodeHin,clean:clean,toHtml:toHtml,toPlain:toPlain,"
            "MONTHS:MONTHS};\n})();\n")


# The order form and both tool pages were written against BNS_VALIDATE's
# contract - {level:'vok'|'vnote'|'vwarn', msg as HTML, fixed}. Rather than
# touch the checkout path, the old name is kept as a thin shim over the shared
# module. Same calls, same return shape, one implementation underneath.
SHIM_JS = r"""
window.BNS_VALIDATE = (function(){
  var D = window.NMB_DECODE;
  function check(raw){
    var r = D.checkRegistration(raw);
    var o = {level: 'v' + r.level};
    if(r.msg) o.msg = D.toHtml(r.msg);
    if(r.fixed) o.fixed = r.fixed;
    if(r.state) o.state = r.state;
    return o;
  }
  return {check: check, clean: D.clean};
})();
"""
