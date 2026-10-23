# -*- coding: utf-8 -*-
"""The lettering preview.

Just the letters, as large as the box allows. The text is drawn into an SVG
whose viewBox is recomputed from the rendered bounding box on every change, so
the glyphs always fill the panel edge to edge regardless of how long the
lettering is or which font is picked.

The panel still flips dark when the vinyl is light, so white, chrome and gold
are always shown against something they can be seen on - that is 33 CFR
173.27's contrast requirement, demonstrated rather than described.
"""

SVG = """
<svg id=prevsvg viewBox="0 0 300 64" role="img" aria-labelledby="prevtitle"
     preserveAspectRatio="xMidYMid meet">
  <title id=prevtitle>Preview of your lettering</title>
  <text id=p_num x="150" y="40" text-anchor="middle"
        font-family="Arial Black, Impact, sans-serif" font-weight="900"
        font-size="34" letter-spacing="1.5" fill="#111">IA 3717 ZW</text>
  <text id=p_name x="150" y="40" text-anchor="middle"
        font-family="Arial Black, Impact, sans-serif" font-weight="900"
        font-size="34" fill="#111">Second Wind</text>
</svg>
"""

CSS = """
.prevwrap{padding:7px 16px 0}
.prev{border-radius:10px;padding:10px 12px;overflow:hidden;background:#e9f0f4;
border:1px solid #cfdde6;transition:background .22s,border-color .22s}
.prev.night{background:#1b2a33;border-color:#0e1b22}
#prevsvg{display:block;width:100%;height:94px}
#p_num,#p_name{transition:fill .2s}
.prevlbl{display:flex;justify-content:center;gap:4px;flex-wrap:wrap;font-size:11.2px;
color:var(--mut);margin-top:5px;font-weight:650;text-align:center}
.prevlbl b{color:var(--ink);font-weight:800}
"""

JS = r"""
window.BNS_PREVIEW = (function(){
  var $=function(i){return document.getElementById(i);};
  var SCRIPTY=/script|vibes|formal|brush/i;
  var PAD=7;           // viewBox units of breathing room around the glyphs
  var BASE_H=94;       // panel height at the 3" baseline, in px
  var LINEGAP=9;

  function render(o){
    var svg=$('prevsvg'); if(!svg) return;
    $('prev').classList.toggle('night', !!o.light);

    // The chosen face, so the big preview and the chip agree.
    var fam = o.css || 'Arial Black, Impact, Haettenschweiler, sans-serif';
    var script = SCRIPTY.test(o.font);
    var style = 'normal';
    var track = script ? '0' : '1.2';
    // On a "Both" order the name can be script but the numbers legally cannot,
    // so the number line is drawn in block regardless. Showing script numbers
    // we would never cut would make the preview a lie.
    var numFam = o.numBlock ? "'Archivo Black','Arial Black',sans-serif" : fam;

    var tn=$('p_num'), nm=$('p_name');
    var both = o.showNum && o.showName;

    [tn,nm].forEach(function(t){
      t.setAttribute('fill', o.hex);
      t.setAttribute('font-family', t===tn ? numFam : fam);
      t.setAttribute('font-style', style);
      t.setAttribute('letter-spacing', (t===tn && o.numBlock) ? '1.2' : track);
      t.setAttribute('font-size', 34);
      t.setAttribute('font-weight', (t===tn && o.numBlock) ? '900'
                                     : (script ? '400' : '900'));
      t.setAttribute('x', 150);
    });

    tn.style.display = o.showNum ? '' : 'none';
    nm.style.display = o.showName ? '' : 'none';
    tn.textContent = o.number || o.placeholder || 'IA 3717 ZW';
    nm.textContent = o.name   || 'Second Wind';

    // Stack the two lines before measuring, otherwise they sit on top of
    // each other and the fitted box is half the height it should be.
    if(both){ tn.setAttribute('y', 30); nm.setAttribute('y', 30 + 34 + LINEGAP); }
    else { tn.setAttribute('y', 40); nm.setAttribute('y', 40); }

    fit(svg, [o.showNum && tn, o.showName && nm].filter(Boolean), o.height);
  }

  /**
   * Fixed panel, scaling glyphs.
   *
   * The panel stays the size it has always been and the lettering grows inside
   * it: 6" fills the panel, 3" renders at half that, 4 and 5 in between. The
   * panel is the hull, so it should not change when the characters do.
   *
   * Done by inflating the viewBox rather than resizing the element - a larger
   * viewBox around the same glyphs renders them smaller. Shrink-wrapping alone
   * always fills the panel in one dimension, which is why every height used to
   * render identically.
   *
   * Text too wide for the panel still shrinks to fit, which is honest: a long
   * name at 6" really will not fit where a short one does.
   */
  function fit(svg, nodes, height){
    var x1=1e9, y1=1e9, x2=-1e9, y2=-1e9, got=false;
    nodes.forEach(function(n){
      var b; try { b=n.getBBox(); } catch(e) { return; }
      if(!b || !b.width) return;
      got=true;
      x1=Math.min(x1,b.x); y1=Math.min(y1,b.y);
      x2=Math.max(x2,b.x+b.width); y2=Math.max(y2,b.y+b.height);
    });
    if(!got){ svg.setAttribute('viewBox','0 0 300 64'); return; }

    var h = Math.max(3, Math.min(6, parseFloat(height) || 3));
    var scale = h / 6;                       // 6" fills the panel, 3" is half

    var gw = (x2 - x1) + PAD * 2, gh = (y2 - y1) + PAD * 2;
    var box = svg.getBoundingClientRect();
    var aspect = (box.width > 0 && box.height > 0)
      ? box.width / box.height : 300 / BASE_H;

    // Inflate the viewBox so the glyphs occupy `scale` of the panel height.
    var vh = gh / scale, vw = vh * aspect;
    // Still too wide at that scale? Let width drive and keep the aspect, so
    // long lettering shrinks instead of spilling out of the panel.
    if (gw > vw) { vw = gw; vh = vw / aspect; }

    var cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
    svg.setAttribute('viewBox',
      (cx - vw / 2)+' '+(cy - vh / 2)+' '+vw+' '+vh);
  }

  return {render: render};
})();
"""
