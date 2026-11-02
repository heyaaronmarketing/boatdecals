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

# The boat view is the default; the flat view is one click away and is where
# someone proofreads their own registration number. Keeping both is deliberate:
# at honest scale a 3" character on six feet of hull is about 16px on screen,
# which is right for "see what it looks like" and wrong for "check my number
# is correct", and a typo there makes the decal worthless.
import pathlib

VIEWS = """
<div class=prevtabs role=tablist>
  <button type=button class="prevtab on" id=viewboat role=tab
          aria-selected=true>On the boat</button>
  <button type=button class=prevtab id=viewflat role=tab
          aria-selected=false>Just the letters</button>
</div>
<div class=boatview id=boatview>
  <img id=plateimg alt="" decoding=async>
  <div class=platetext id=platetext><span id=platespan></span></div>
</div>
<div class=platenote id=platenote></div>
"""

def data_js():
    """The plate table, straight from the file media/plates.py writes.

    One source of truth: the calibration that crops the images is the same
    calibration the browser positions text with. A plate whose `inches` drifted
    from the crop it was measured against would put the lettering at a scale
    the photograph does not support.
    """
    import json
    f = pathlib.Path(__file__).resolve().parent / "plates.json"
    rows = json.loads(f.read_text())
    return "window.BNS_PLATES=%s;" % json.dumps(rows, separators=(",", ":"))


SVG = """
<svg id=prevsvg viewBox="0 0 300 64" role="img" aria-labelledby="prevtitle"
     preserveAspectRatio="xMidYMid meet">
  <title id=prevtitle>Preview of your lettering</title>
  <text id=p_num x="150" y="40" text-anchor="middle"
        font-family="Arial Black, Impact, sans-serif" font-weight="900"
        font-size="34" letter-spacing="1.5" fill="#111">IA 3717 ZW</text>
  <text id=p_name x="150" y="40" text-anchor="middle" style="display:none"
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

.prevtabs{display:flex;gap:5px;margin-bottom:7px}
.prevtab{flex:1;font:inherit;font-size:11.4px;font-weight:800;cursor:pointer;
background:#fff;border:1.5px solid var(--line);border-radius:8px;padding:5px 8px;
color:var(--mut);transition:border-color .12s,background .12s,color .12s}
.prevtab.on{background:var(--nav);border-color:var(--nav);color:#fff}

/* The photo and the lettering share one positioning context, so the text can
   be placed in fractions of the plate rather than in pixels - the same numbers
   hold at every panel width. */
.boatview{position:relative;border-radius:10px;overflow:hidden;
border:1px solid #cfdde6;background:#e9f0f4;line-height:0}
.boatview img{display:block;width:100%;height:auto}
.platetext{position:absolute;left:0;top:0;width:100%;height:100%;
pointer-events:none}
#platespan{position:absolute;white-space:nowrap;line-height:1;
transform-origin:left top}
/* Dark vinyl multiplies so the hull's scuffs and shading read through it, the
   way film on gelcoat actually looks. Light vinyl is opaque, so it does not. */
#platespan.ink{mix-blend-mode:multiply}
.platenote{font-size:10.6px;color:var(--mut);margin-top:5px;text-align:center;
font-weight:650}
.platenote b{color:var(--ink);font-weight:800}
.platenote[hidden]{display:none}
"""

JS = r"""
window.BNS_PREVIEW = (function(){
  var $=function(i){return document.getElementById(i);};
  var PAD=7;           // viewBox units of breathing room around the glyphs
  var BASE_H=94;       // panel height at the 3" baseline, in px
  var LINEGAP=9;

  function render(o){
    var svg=$('prevsvg'); if(!svg) return;
    // With an outline it is the OUTLINE that touches the hull, so that is the
    // color the panel has to contrast with, not the fill.
    $('prev').classList.toggle('night', o.outline ? !!o.outlineLight : !!o.light);

    // The chosen face, so the big preview and the chip agree.
    var fam = o.css || 'Arial Black, Impact, Haettenschweiler, sans-serif';
    // Looked up at call time, not at init: BNS_FONTCAT is assigned further
    // down the page than this IIFE, so caching it here would cache {}.
    var script = (window.BNS_FONTCAT||{})[o.font]==='script';
    var style = 'normal';
    var track = script ? '0' : '1.2';
    // On a "Both" order the name can be script but the numbers legally cannot,
    // so the number line is drawn in block regardless. Showing script numbers
    // we would never cut would make the preview a lie.
    var numFam = o.numBlock ? "'Archivo Black','Arial Black',sans-serif" : fam;

    var tn=$('p_num'), nm=$('p_name');
    var both = o.showNum && o.showName;

    // The outline is drawn as a stroke BEHIND the glyph (paint-order), which
    // is exactly what the second layer of vinyl does on the hull - cut a
    // little larger and sat under the characters.
    [tn,nm].forEach(function(t){
      t.setAttribute('fill', o.hex);
      if(o.outline){
        t.setAttribute('stroke', o.outlineHex);
        t.setAttribute('stroke-width', 5);
        t.setAttribute('paint-order', 'stroke fill');
        t.setAttribute('stroke-linejoin', 'round');
      } else {
        t.removeAttribute('stroke');
        t.removeAttribute('stroke-width');
        t.removeAttribute('paint-order');
      }
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
    boat(o);
  }

  /**
   * The same lettering, on a photograph of a hull, at honest scale.
   *
   * Each plate declares how many inches of real hull its WIDTH spans, so
   * character height is a fraction of the plate - `inches / plate.inches` -
   * and holds at any panel width without a second calibration. The plates are
   * shot square-on and their rub rails are level to within a degree, so a flat
   * rotate + translate is enough; there is no perspective to undo.
   */
  function boat(o){
    var wrap=$('boatview'), img=$('plateimg'), span=$('platespan');
    if(!wrap || !img || !span) return;
    var plates=window.BNS_PLATES;
    if(!plates || !plates.length){ wrap.hidden=true; return; }

    // Registration numbers go on the bow, a name goes on the transom. A "Both"
    // order shows the side: the numbers are the half with a legal placement
    // rule, and the font hint already explains where the name lands.
    var view = (o.showName && !o.showNum) ? 'transom' : 'side';
    // The hull has to contrast with the vinyl, which is the whole point of
    // 33 CFR 173.27 - white film needs the dark plate to be visible at all.
    // With an outline it is the OUTLINE that touches the hull.
    var lightFilm = o.outline ? !!o.outlineLight : !!o.light;
    var p=null;
    for(var i=0;i<plates.length;i++){
      if(plates[i].view===view && !!plates[i].dark===lightFilm){ p=plates[i]; break; }
    }
    if(!p){ wrap.hidden=true; return; }
    wrap.hidden=false;

    if(img.getAttribute('data-plate')!==p.id){
      img.setAttribute('data-plate', p.id);
      img.src='/assets/img/'+p.id+'-800.webp';
    }

    var text = view==='transom' ? (o.name || 'Second Wind')
                                : (o.number || o.placeholder || 'IA 3717 ZW');
    span.textContent=text;

    var inches = Math.max(3, Math.min(6, parseFloat(o.height) || 3));
    var boxW = wrap.clientWidth || 1;
    // Cap height, not font-size: the law measures the characters themselves,
    // and a face's cap height is a fraction of its em that varies per family.
    var capPx = inches / p.inches * boxW;
    span.style.fontFamily = o.css || "'Archivo Black',sans-serif";
    span.style.fontWeight = (view==='side' && o.numBlock) ? '900' : '';
    span.style.fontSize = (capPx / capRatio(span, o.css)) + 'px';
    span.style.color = o.hex;
    span.style.letterSpacing = (view==='side' ? capPx*0.06 : 0) + 'px';
    span.style.webkitTextStroke = o.outline
      ? (capPx*0.09)+'px '+o.outlineHex : '';
    span.style.paintOrder = 'stroke fill';
    // Vector type on a photograph reads as pasted on; real film has a hair of
    // edge softness and the plate has sensor noise. Scaled to cap height so it
    // stays the same relative softness at any panel width, and capped - past
    // about half a pixel it stops looking like vinyl and starts looking
    // out of focus.
    span.style.filter = 'blur(' + Math.min(0.55, capPx * 0.012) + 'px)';
    span.classList.toggle('ink', !lightFilm);

    // Anchor is a fraction of the plate; `left` aligns bow numbers forward,
    // `center` centres a transom name.
    var ax=p.anchor[0]*boxW, ay=p.anchor[1]*(wrap.clientHeight||1);
    span.style.left=ax+'px'; span.style.top=ay+'px';
    span.style.transform='rotate('+(p.deg||0)+'deg)'
      + (p.align==='center' ? ' translateX(-50%)' : '');

    note(p, span, inches, boxW);
  }

  /**
   * Cap height as a fraction of font-size, measured rather than assumed.
   *
   * A name with ascenders and descenders ("Sea Ya Later") has a bounding box
   * taller than its capitals, so sizing from the rendered box would make every
   * script face read small. Measuring a lone "H" in the same family gives the
   * real cap ratio, and it is cached per family.
   */
  var CAPS={};
  function capRatio(span, css){
    var k=css||'default';
    if(CAPS[k]) return CAPS[k];
    var probe=document.createElement('span');
    probe.textContent='H';
    probe.style.cssText='position:absolute;visibility:hidden;font-size:200px;'
      + 'line-height:1;white-space:nowrap;font-family:'+(css||'sans-serif');
    document.body.appendChild(probe);
    var r=probe.getBoundingClientRect().height/200;
    probe.remove();
    // A face that has not downloaded yet measures against the fallback, so do
    // not cache an obviously wrong ratio - it would stick for the session.
    if(!(r>0.4 && r<1.2)) return 0.72;
    CAPS[k]=r; return r;
  }

  /** Finished size, derived from the glyphs actually on screen. */
  function note(p, span, inches, boxW){
    var el=$('platenote'); if(!el) return;
    var w=span.getBoundingClientRect().width;
    if(!w){ el.hidden=true; return; }
    el.hidden=false;
    var long=Math.round(w / boxW * p.inches);
    el.innerHTML='About <b>'+long+'&quot; long &times; '+inches
      +'&quot; tall</b> &middot; shown to scale on a '+p.nominal;
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

  function showView(boatOn){
    var b=$('boatview'), f=$('prev'), n=$('platenote');
    if(!b||!f) return;
    b.hidden=!boatOn; f.hidden=!!boatOn;
    if(n) n.hidden=!boatOn;
    var vb=$('viewboat'), vf=$('viewflat');
    if(vb){ vb.classList.toggle('on', boatOn);
            vb.setAttribute('aria-selected', boatOn?'true':'false'); }
    if(vf){ vf.classList.toggle('on', !boatOn);
            vf.setAttribute('aria-selected', boatOn?'false':'true'); }
  }

  var vb=$('viewboat'), vf=$('viewflat');
  if(vb) vb.addEventListener('click', function(){ showView(true); });
  if(vf) vf.addEventListener('click', function(){ showView(false); });
  showView(true);

  // The plate image arrives after first paint, and the lettering is positioned
  // against the plate's rendered height - so place it again once that is real.
  var pi=$('plateimg');
  if(pi) pi.addEventListener('load', function(){ if(LAST) boat(LAST); });
  var LAST=null;
  addEventListener('resize', function(){ if(LAST) boat(LAST); });

  return {render: function(o){ LAST=o; render(o); }};
})();
"""
