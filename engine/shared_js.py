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


def _fn(src, name):
    """One named export out of a JS module, by brace matching.

    Used to lift `widthIn` out of worker/gates.js rather than copying it. The
    alternative - a second width function written for the browser - is the bug
    this repo exists to not have: the order form would quote a name in one
    band while the worker charged another, and the customer would be holding
    the screenshot. verify.py checks that what lands in the page is still
    character-for-character what is in the worker file.
    """
    i = src.index("export function %s(" % name)
    j = src.index("{", i)
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1].replace("export function", "function", 1)
    raise AssertionError("unbalanced braces reading %s" % name)


def price_js():
    """The pricing function, as a browser IIFE exposing window.NMB_PRICE.

    THE POINT. The order form shows a running total from step 1, and the
    button says "Pay $71". The worker charges what IT calculates and never
    what the browser posts - which is right, but it means the two have to
    agree, and for a year they agreed only because a human kept two copies of
    the same arithmetic in step. They did not always: the form's own total
    fell through to the base price for a bundle, so a six-inch pair with an
    outline displayed as the cheapest thing in the shop.

    Now there is one implementation. worker/price.js is inlined here, with the
    generated price table and the one width function it needs, and the figure
    on the button is produced by the same code that produces the figure on the
    card. A disagreement is no longer possible, so it no longer needs testing
    for - which is a better outcome than a test.
    """
    import json

    data = (ROOT / "worker" / "price-data.js").read_text(encoding="utf-8")
    logic = (ROOT / "worker" / "price.js").read_text(encoding="utf-8")
    gates = (ROOT / "worker" / "gates.js").read_text(encoding="utf-8")
    gdata = (ROOT / "worker" / "gates-data.js").read_text(encoding="utf-8")

    data = _strip_module(data, drop_import=False)
    data = data.replace("const P = ", "var P = ", 1)

    # The WHOLE table, upgrade prices included. The first version of this
    # stripped UPGRADE_ADD out, because one upgrade label carried a
    # film-life year figure and inlining it would have published that figure
    # on thirty pages - which verify.py's claims gate caught. Stripping it
    # worked only because the form renders no upgrades step, so it left the
    # form and the card disagreeing about the price of any order that had
    # one, conditional on a feature nobody had built yet. The upgrade was
    # renamed instead. If the form ever grows that step, the running total
    # will already be right.

    # Only the font metrics, not the whole gates bundle. The order form has no
    # use for the rebus tokens or the 1,089-name overuse tiers, and the page
    # is already heavy.
    body = gdata[gdata.index("{"):gdata.rindex(";")]
    fonts = json.loads(body)["FONTS"]

    return ("/* SHARED: worker/price.js + the widthIn() from worker/gates.js,\n"
            "   inlined by engine/shared_js.price_js(). One implementation -\n"
            "   edit the worker files, not this. The price table itself comes\n"
            "   from engine/content.py via mcp/build_price_js.py. */\n"
            "(function(){\n"
            + data + "\n"
            + "var D = {FONTS: " + json.dumps(fonts, sort_keys=True) + "};\n"
            + _fn(gates, "widthIn") + "\n"
            + _strip_module(logic) + "\n"
            "window.NMB_PRICE={priceOf:priceOf,breakdown:priceBreakdown,"
            "nameBand:nameBand,FROM:FROM,OUTLINE_ADD:OUTLINE_ADD};\n})();\n")
