# -*- coding: utf-8 -*-
"""The boat preview.

A flat colour swatch could not answer the two questions people actually have -
"will this read against my hull?" and "where does it go?" - so the preview is a
hull in side profile with the lettering placed where it legally belongs:

  registration numbers -> forward half, with the validation decal aft of them
  boat name            -> transom, at the stern
  both                 -> both, which is the clearest possible argument for the
                          $44 bundle

The hull fill flips with the vinyl's lightness, so light vinyl is always shown
on a dark hull and dark vinyl on a light one. That is the federal contrast rule
(33 CFR 173.27) demonstrated rather than described.
"""

# Side profile, bow to the left. Kept to one path so the fill can be swapped in
# one write, and viewBox'd so it scales to any panel width.
SVG = """
<svg id=hullsvg viewBox="0 0 340 128" role="img" aria-labelledby="hulltitle"
     preserveAspectRatio="xMidYMid meet">
  <title id=hulltitle>Preview of your lettering on a boat</title>
  <defs>
    <clipPath id="hullclip">
      <path d="M10 34 C46 25 140 21 318 24 L316 76 C315 88 306 95 293 95
               L74 95 C46 95 24 70 12 46 Z"/>
    </clipPath>
  </defs>

  <!-- water -->
  <path id=hullwater d="M0 96 C40 92 70 100 110 97 C150 94 185 101 226 98
           C266 95 300 101 340 97 L340 128 L0 128 Z" fill="#cfe0ea" opacity=".85"/>
  <path id=hullwave d="M0 104 C44 100 76 108 118 105 C158 102 196 109 238 106
           C276 103 306 109 340 105" fill="none" stroke="#a9c7d8" stroke-width="1.6"/>

  <!-- hull -->
  <path id=hullbody d="M10 34 C46 25 140 21 318 24 L316 76 C315 88 306 95 293 95
           L74 95 C46 95 24 70 12 46 Z" fill="#e9f0f4" stroke="#b9ccd8" stroke-width="1.5"/>
  <!-- rub rail, and a windscreen so it reads as a boat at a glance -->
  <path id=hullrail d="M11 38 C48 29 140 25 317 28" fill="none"
        stroke="#b9ccd8" stroke-width="2.4" stroke-linecap="round"/>
  <path id=hullscreen d="M243 24 L262 7 L286 7 L288 24 Z" fill="#b9ccd8" opacity=".55"/>

  <g clip-path="url(#hullclip)">
    <!-- forward half: registration numbers + validation decal -->
    <g id=g_num>
      <text id=t_num x="104" y="66" text-anchor="middle"
            font-family="Arial Black, Impact, sans-serif" font-weight="900"
            font-size="19" letter-spacing="1.1" fill="#111">IA 3717 ZW</text>
      <rect id=t_decal x="170" y="55" width="15" height="13" rx="2.5" fill="#111" opacity=".55"/>
    </g>
    <!-- stern: the boat name on the transom -->
    <text id=t_name x="258" y="68" text-anchor="middle"
          font-family="Arial Black, Impact, sans-serif" font-weight="900"
          font-size="15" fill="#111">Second Wind</text>
  </g>
</svg>
"""

CSS = """
.prevwrap{padding:7px 16px 0}
.prev{border-radius:10px;padding:3px 6px 0;overflow:hidden;
background:linear-gradient(#eaf3f8,#dceaf2);transition:background .22s}
.prev.night{background:linear-gradient(#20323d,#16242c)}
#hullsvg{display:block;width:100%;height:auto;max-height:84px}
#t_num,#t_name,#t_decal,#hullbody,#hullrail,#hullscreen,#hullwater,#hullwave
{transition:fill .2s,stroke .2s}
/* Night is not just the hull - the water has to come with it or the boat
   looks like it is floating on a light strip. */
.prev.night #hullwater{fill:#24404f}
.prev.night #hullwave{stroke:#375d70}
.prevlbl{display:flex;justify-content:center;gap:4px;flex-wrap:wrap;font-size:11.2px;
color:var(--mut);margin-top:4px;font-weight:650;text-align:center}
.prevlbl b{color:var(--ink);font-weight:800}
"""

JS = r"""
window.BNS_HULL = (function(){
  var $=function(i){return document.getElementById(i);};
  // Hull + trim, keyed to whether the vinyl is light or dark.
  var SKIN={
    light:{body:'#223642', rail:'#33505f', screen:'#33505f', stroke:'#16242c'},
    dark :{body:'#eef5f9', rail:'#b9ccd8', screen:'#b9ccd8', stroke:'#b9ccd8'}
  };
  var SCRIPTY=/script|vibes|lobster|old english/i;

  // Shrink to fit the panel rather than overflow the hull.
  function fit(el, text, maxW, base){
    el.textContent=text;
    el.setAttribute('font-size', base);
    var w;
    try { w = el.getComputedTextLength(); } catch(e) { w = 0; }
    if(w > maxW && w > 0) el.setAttribute('font-size', Math.max(7, base*maxW/w));
  }

  function render(o){
    var stage=$('prev'), svg=$('hullsvg');
    if(!svg) return;
    var skin = o.light ? SKIN.light : SKIN.dark;
    stage.classList.toggle('night', !!o.light);
    $('hullbody').setAttribute('fill', skin.body);
    $('hullbody').setAttribute('stroke', skin.stroke);
    $('hullrail').setAttribute('stroke', skin.rail);
    $('hullscreen').setAttribute('fill', skin.screen);

    var fam = SCRIPTY.test(o.font)
      ? 'Georgia, "Times New Roman", serif'
      : 'Arial Black, Impact, Haettenschweiler, sans-serif';
    var style = SCRIPTY.test(o.font) ? 'italic' : 'normal';

    var gn=$('g_num'), tn=$('t_num'), nm=$('t_name'), dc=$('t_decal');
    gn.style.display = o.showNum ? '' : 'none';
    nm.style.display = o.showName ? '' : 'none';

    if(o.showNum){
      tn.setAttribute('fill', o.hex);
      tn.setAttribute('font-family', fam);
      tn.setAttribute('font-style', style);
      dc.setAttribute('fill', o.hex);
      fit(tn, o.number || 'IA 3717 ZW', o.showName ? 112 : 150, 19);
      // The decal sits just aft of the number, which is where most states want it.
      var bb;
      try { bb = tn.getBBox(); } catch(e) { bb = null; }
      if(bb){ dc.setAttribute('x', Math.min(bb.x + bb.width + 9, 300)); }
    }
    if(o.showName){
      nm.setAttribute('fill', o.hex);
      nm.setAttribute('font-family', fam);
      nm.setAttribute('font-style', style);
      // A name alone can use the whole transom; sharing with numbers it cannot.
      nm.setAttribute('x', o.showNum ? 262 : 196);
      fit(nm, o.name || 'Second Wind', o.showNum ? 92 : 200, o.showNum ? 14 : 20);
    }
  }
  return {render: render};
})();
"""
