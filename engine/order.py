# -*- coding: utf-8 -*-
"""The order wizard - this site's only conversion element.

Four steps, one decision each, in a fixed-height shell so the page never jumps:

  1. What do you need?      three cards, auto-advances on click (no typing)
  2. What should it say?    lettering + font; the only step that demands typing
  3. How should it look?    clicks only; the preview flips its panel dark so
                            light vinyl always renders on dark and vice versa
  4. Checkout               Stripe Payment Element, embedded

There is deliberately no upsell step. The add-ons on /pricing/ are requested in
the checkout notes box instead - the worker still prices them, so a note-added
upgrade costs the same as a clicked one would have.

Anti-fatigue rules this file holds to:
  - never more than one required text field per step
  - steps 1, 3 and 4 are pure clicking
  - name/phone/boat/notes are optional or collapsed; the card supplies the name
  - the running total is visible from step 1 so the price is never a late surprise

Price is computed here for instant feedback and RE-COMPUTED in worker/index.js,
which is the authority. Never trust a posted total.
"""
from content import (PRICE, FONTS, COLORS, ORDER_COLORS, STATES, UPGRADES,
                     google_fonts_href)
import preview as PV

# (inches, price add, label). The old fourth field held a one-word pitch
# ("legal minimum", "reads better") under each box; the size and the price are
# the whole decision, so the boxes got bigger and the captions went.
HEIGHTS = [(3, 0, "3&quot;"), (4, 4, "4&quot;"), (5, 8, "5&quot;"),
           (6, 13, "6&quot;")]

# (value, base, price, flag, key, label)
#
# `value` is what the radio submits and must not drift: worker/index.js prices
# on it (BASE), gates script fonts on it, and every order already in D1 carries
# it. `label` is only what the customer reads, and is worded to match the header
# nav ("Boat Numbers", "Boat Letters") rather than the internal product names.
#
# There was a caption line too ("On the bow, both sides", "On the transom").
# The thumbnail already shows where the lettering goes, so it was the icon in
# words - the name and the price are the whole decision.
KINDS = [
    ("Registration numbers", 19, "$19", "", "numbers", "Boat Numbers"),
    ("Boat name", 29, "$29+", "", "name", "Boat Name"),
    ("Both", 44, "$44+", "Save $4", "both", "Both"),
]

_KICON = {
    # hash = numbers
    "numbers": '<path d="M9.2 3.5L7 20.5M17.2 3.5L15 20.5M4 8.8h15.4M3.2 15.2h15.4" '
               'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" fill="none"/>',
    # a letterform = a name
    "name": '<path d="M4 19.5L12 4.5l8 15M7.6 14.4h8.8" stroke="currentColor" '
            'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
    # two plates = both
    "both": '<rect x="3.6" y="4.6" width="16.8" height="6" rx="1.8" stroke="currentColor" '
            'stroke-width="1.8" fill="none"/>'
            '<rect x="3.6" y="13.4" width="16.8" height="6" rx="1.8" stroke="currentColor" '
            'stroke-width="1.8" fill="none"/>',
}

def _thumb(key):
    return ('<span class=kicon><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>'
            % _KICON[key])


def _colors(prefix="color", checked="Black"):
    """Eight chips in a row. That is the whole control.

    The name is NOT printed under every chip - eight labels is eight things to
    read before picking a color. The chip you have selected is named once, in
    the line underneath, and the preview above is already showing it on your
    own lettering. Each input still carries an aria-label so a screen reader
    gets the name without the sighted layout paying for it.
    """
    picks = [c for c in COLORS if c[0] in ORDER_COLORS]
    picks.sort(key=lambda c: ORDER_COLORS.index(c[0]))
    return "".join(
        '<label class=csw title="%s"><input type=radio name="%s" value="%s" '
        'data-hex="%s" data-light="%d" aria-label="%s"%s>'
        '<span class=cswdot style="background:%s"></span></label>'
        % (name, prefix, name, hexv, light, name,
           " checked" if name == checked else "", hexv)
        for name, hexv, light in picks)


def form():
    # Each chip renders the customer's own lettering in that face, so the
    # choice is made on the thing itself rather than on a font name.
    fonts = "".join(
        '<label class=fontchip data-block="%d" title="%s">'
        '<input type=radio name=font value="%s"%s aria-label="%s">'
        '<span class=fontbox><span class=fontdemo style="font-family:%s">%s</span>'
        '</span></label>'
        % (1 if block else 0, lbl, lbl, "", lbl,
           css.replace('"', "&quot;"), "Abc")
        for i, (lbl, css, _g, block, _match) in enumerate(FONTS))
    # Tabs, so 72 faces read as three manageable sets rather than one wall -
    # and so only the set you are looking at has to download.
    heights = "".join(
        '<label class=opt><input type=radio name=height value="%d" data-add="%d"%s>'
        '<span class=optbox>%s</span>'
        '<em class=optcap><i>%s</i></em></label>'
        % (h, add, " checked" if h == 3 else "", lbl,
           "included" if add == 0 else "+$%d" % add)
        for h, add, lbl in HEIGHTS)
    kinds = "".join(
        '<label class=kind><input type=radio name=kind value="%s" data-base="%d"%s>'
        '<span class=kindbox>%s%s<b>%s</b><i>%s</i></span></label>'
        % (val, base, " checked" if key == "numbers" else "",
           '<span class=flag>%s</span>' % flag if flag else "",
           _thumb(key), label, price)
        for val, base, price, flag, key, label in KINDS)
    cols = _colors()

    markup = ("""
<div id=order class="panel wiz">
  <div class=wizhead>
    <div class=wizbar><i id=wizfill></i></div>
    <div class=wizmeta>
      <button type=button class=wizback id=back hidden>&larr; Back</button>
      <span id=stepnum>Step 1 of __STEPS__</span>
      <span class=wiztot>
        <span class=wiztotrow>Total <b id=total>$19</b></span>
        <em>Free shipping</em>
      </span>
    </div>
  </div>

  <div class=prevwrap id=prevwrap>
__VIEWS__
    <div class=prev id=prev aria-live=polite>__HULL__</div>
    <div class=prevlbl id=prevlbl></div>
  </div>

  <div class=wizbody>

  <!-- 1 ------------------------------------------------------------- -->
  <section class="step on" data-step="1" data-when="">
    <h2>What do you need?</h2>
    
    <div class=kinds>""" + kinds + """</div>
  </section>

  <!-- 2 - the registration number, only when one is being cut -------- -->
  <section class=step data-step="2" data-when="num">
    <h2>What is the number?</h2>
    <label for=f_text>Registration number</label>
    <input type=text id=f_text name=text value="" placeholder="IA 3717 ZW"
           autocomplete=off maxlength=40 autocapitalize=characters spellcheck=false>
    <div class=vcheck id=vcheck role=status aria-live=polite></div>
    <div class=err id=e2 role=alert></div>
  </section>

  <!-- 3 - the boat name, only when one is being cut ------------------ -->
  <section class=step data-step="3" data-when="name">
    <h2>What is she called?</h2>
    <label for=f_name2>Boat name</label>
    <input type=text id=f_name2 name=boatname value="" placeholder="Second Wind"
           autocomplete=off maxlength=40 spellcheck=false>
    <div class=hint>We cut it exactly as typed, so capitals matter. Stuck?
      <a href="/tools/boat-name-generator/" target="_blank"
         rel="noopener">1,000 name ideas</a>.</div>
    <div class=err id=e3 role=alert></div>
  </section>

  <!-- 4 - font ------------------------------------------------------- -->
  <section class=step data-step="4" data-when="">
    <h2>Pick a font</h2>
    <div class=fontgrid id=fontgrid>""" + fonts + """</div>
    <div class=err id=e4 role=alert></div>
    <div class=hint id=fonthint></div>
  </section>

  <!-- 5 - color, and the outline upsell ------------------------------ -->
  <section class=step data-step="5" data-when="">
    <h2>Pick a color</h2>
    <div class=swrow id=swrow>""" + cols + """</div>

    <label class=outline-opt>
      <input type=checkbox id=f_outline name=outline value="1">
      <span class=outbox>
        <span class=outbox-check aria-hidden="true"></span>
        <b>Add outline</b>
        <em>A second layer of vinyl cut behind every character</em>
      </span>
      <i class=outprice>+$""" + str(PRICE["outline"]) + """</i>
    </label>

    <div id=outrow class=outrow hidden>
      <div class=outlabel>Outline color</div>
      <div class=swrow>""" + _colors("outline_color", "White") + """</div>
    </div>
  </section>

  <!-- 6 - character height ------------------------------------------- -->
  <section class=step data-step="6" data-when="">
    <h2>How tall?</h2>
    <div class=opts>""" + heights + """</div>

  </section>

  <!-- 7 - checkout --------------------------------------------------- -->
  <section class=step data-step="7" data-when="">
    <h2>Checkout</h2>
    <div class=sumbox id=summary></div>
    <div class="fieldrow two">
      <div><label for=f_email>Email</label>
        <input type=email id=f_email name=email autocomplete=email
               placeholder="you@example.com" inputmode=email>
        <div class=hint>Proof and receipt go here.</div></div>
      <div><label for=f_name>Name</label>
        <input type=text id=f_name name=name autocomplete=name placeholder="Jane Rivera">
      </div>
    </div>
    <div id=paywrap style="margin-top:15px">
      <div id=payelement class=payel></div>
      <div class=hint id=payhint>Secured by Stripe. We never see your card number.</div>
    </div>
    <div class=err id=e5 role=alert></div>
  </section>

  </div>

  <div class=wizfoot>
    <button type=button class="btn lg" id=next>Continue</button>
  </div>
</div>""")

    # The step label and the progress bar both derive from how many <section
    # class=step> blocks are actually in the markup. A hand-kept "of 5" is how
    # the header went on claiming five steps a month after step 4 was removed.
    steps = markup.count('class=step ') + markup.count('class="step on"')
    return (markup.replace("__VIEWS__", PV.VIEWS)
                  .replace("__HULL__", PV.SVG)
                  .replace("__STEPS__", str(steps)))


def color_js():
    cols = ",".join('"%s":["%s",%d]' % (n, h, l) for n, h, l in COLORS)
    prefixes = ",".join('"%s":"%s"' % (st["ab"], st["name"]) for st in STATES)
    fontcss = ",".join('"%s":"%s"' % (lbl, css.replace('"', "'"))
                       for lbl, css, _g, _b, _m in FONTS)
    # preview.py keys letter-spacing off this. It used to sniff the label for
    # "script"/"brush", which missed most of the connected faces and tracked
    # their joins apart. None of the current ten are connected scripts, so
    # every one tracks like a block face - but the map stays, because the day
    # a script is added the tracking has to follow it without a code change.
    fontcat = ",".join('"%s":"%s"' % (lbl, "block" if block else "display")
                       for lbl, _c, _g, block, _m in FONTS)
    return ("window.BNS_COL={%s};window.BNS_PREFIX={%s};window.BNS_FONTCSS={%s};"
            "window.BNS_FONTCAT={%s};"
            % (cols, prefixes, fontcss, fontcat))


JS = r"""
(function(){
  var W=document.getElementById('order'); if(!W) return;
  var COL=window.BNS_COL||{};
  var steps=[].slice.call(W.querySelectorAll('.step'));
  // `cur` is the step's stable data-step id, NOT its position. Two of the
  // seven steps appear only when they apply - there is no "what is the
  // number" step on a name-only order - so a positional index would point at
  // a different question every time the kind changed. Position is derived.
  var cur=1;

  function visible(){
    return steps.filter(function(s){
      var w=s.dataset.when;
      return !w || (w==='num' ? isNum() : hasName());
    });
  }
  function ids(){ return visible().map(function(s){ return +s.dataset.step; }); }
  // What the NEXT step asks, so the button says where it goes rather than
  // just "Continue". A form whose end you cannot see gets abandoned.
  function nextLabel(){
    var n = stepAfter(cur);
    if(n === cur) return 'Continue';
    var map = {2:'Next: the number', 3:'Next: the name', 4:'Next: pick a font',
               5:'Next: pick a color', 6:'Next: how tall', 7:'Next: checkout'};
    return map[n] || 'Continue';
  }
  function pos(){ var i=ids().indexOf(cur); return i<0 ? 1 : i+1; }
  function total(){ return visible().length; }
  function lastId(){ var a=ids(); return a[a.length-1]; }
  function isLast(){ return cur===lastId(); }
  function stepAfter(n){ var a=ids(), i=a.indexOf(n); return a[Math.min(i+1,a.length-1)]; }
  function stepBefore(n){ var a=ids(), i=a.indexOf(n); return a[Math.max(i-1,0)]; }
  var PLACEHOLDER='IA 3717 ZW';   // replaced by the visitor's own state
  var $=function(id){return document.getElementById(id);};
  var nextBtn=$('next'), backBtn=$('back'), fill=$('wizfill'),
      stepnum=$('stepnum'), tot=$('total');
  var stripe=null, elements=null, clientSecret=null, mounted=false,
      paying=false, sandbox=false;

  function kind(){var r=W.querySelector('[name=kind]:checked');return r?r.value:'Registration numbers';}

  /** The registration number carries its own state prefix, so asking for the
   *  state again was a field for data we already had. CF=California,
   *  WN=Washington, otherwise the two-letter postal code. */
  /**
   * Seed the placeholders with the visitor's own state prefix.
   *
   * Placeholder only - they still type their real number off the card, so a
   * wrong guess costs nothing. That is why there is no retry and no fallback:
   * if the call fails we keep the Iowa default and move on.
   *
   * Never overwrites something already typed.
   */
  function seedStatePrefix(){
    var cached;
    try { cached = sessionStorage.getItem('bns_prefix'); } catch(e) {}
    if(cached){ applyPrefix(cached); return; }
    fetch('/api/geo').then(function(r){ return r.json(); }).then(function(g){
      if(!g || !g.code) return;
      try { sessionStorage.setItem('bns_prefix', g.code); } catch(e) {}
      applyPrefix(g.code);
    }).catch(function(){});
  }

  function applyPrefix(code){
    if(!/^[A-Z]{2}$/.test(code)) return;
    PLACEHOLDER = code + ' 3717 ZW';
    var t=$('f_text');
    if(t && !t.value.trim()) t.placeholder = PLACEHOLDER;
    render();
  }

  function stateFromPrefix(){
    var m=($('f_text').value||'').trim().toUpperCase().match(/^([A-Z]{2})/);
    // VESSEL prefixes, not postal codes: MS is Massachusetts, MI is
    // Mississippi, MC is Michigan. A postal lookup gets two of those wrong.
    return (m && (window.BNS_PREFIX_STATE||{})[m[1]]) || '';
  }
  function isNum(){return kind()!=='Boat name';}
  function hasName(){return kind()!=='Registration numbers';}
  function val(n){var el=W.querySelector('[name='+n+']:checked');return el||null;}

  function price(){
    var k=W.querySelector('[name=kind]:checked');
    var n=k?parseFloat(k.dataset.base):19;
    var h=val('height'); if(h) n+=parseFloat(h.dataset.add||0);
    if(hasOutline()) n+=OUTLINE_ADD;
    var ups=W.querySelectorAll('[name=upgrade]:checked');
    for(var i=0;i<ups.length;i++) n+=parseFloat(ups[i].dataset.add||0);
    return Math.round(n);
  }

  /** What we would actually cut: the corrected spacing, not the raw typing. */
  function numberForPreview(){
    var raw=($('f_text').value||'').trim();
    if(!raw || !window.BNS_VALIDATE) return raw;
    var v=window.BNS_VALIDATE.check(raw);
    return v.fixed || raw;
  }

  var OUTLINE_ADD=12;
  function hasOutline(){ var b=$('f_outline'); return !!(b && b.checked); }

  /** The outline color is a SECOND decision, so it answers itself first.
   *
   *  Turning the checkbox on picks the obvious contrast - white behind dark
   *  letters, black behind light ones - so a customer who never touches the
   *  second row still gets the right answer. The row is there to override,
   *  not to be filled in.
   */
  function syncOutline(){
    var on=hasOutline();
    $('outrow').hidden=!on;
    if(!on) return;
    var picked=W.querySelector('[name=outline_color]:checked');
    if(picked && picked.dataset.auto!=='1') return;      // customer chose
    var c=val('color'), meta=COL[c?c.value:'Black']||['#111111',0];
    var want=meta[1] ? 'Black' : 'White';                // light fill -> dark
    var el=W.querySelector('[name=outline_color][value="'+want+'"]');
    if(el){ el.checked=true; el.dataset.auto='1'; }
  }

  function renderPreview(){
    var lbl=$('prevlbl'); if(!lbl || !window.BNS_PREVIEW) return;
    var c=val('color'), cname=c?c.value:'Black';
    var isOut=hasOutline();
    var oc=val('outline_color'), ocn=oc?oc.value:'White';
    var ometa=COL[ocn]||['#ffffff',1];
    var meta=COL[cname]||['#111111',0];
    var h=val('height'), hv=h?h.value:'3';
    var fn=font();
    window.BNS_PREVIEW.render({
      hex: meta[0], light: !!meta[1], font: fn, height: hv,
      css: (window.BNS_FONTCSS||{})[fn] || '',
      numBlock: isNum() && hasName() && !isBlockFont(fn),
      showNum: isNum(), showName: hasName(),
      number: numberForPreview(), placeholder: PLACEHOLDER,
      name: ($('f_name2').value||'').trim(),
      outline: isOut, outlineHex: ometa[0], outlineLight: !!ometa[1]
    });
    lbl.innerHTML = '<b>'+hv+'&quot;</b> '+(fn ? esc(fn) : 'font not picked yet')+
      ' &middot; <b>'+esc(cname)+'</b>'+
      (isOut ? ' with <b>'+esc(ocn)+'</b> outline' : '')+' &middot; '+
      (isNum() ? (hasName()? 'pair + name, pre-spaced' : 'one pair, pre-spaced')
               : 'one decal, pre-spaced');
  }

  // Empty until the customer picks one. Nothing is preselected: a default
  // here is a choice nobody made, and it is the one field the whole order is
  // cut from. Callers that need something to DRAW fall back on their own.
  function font(){
    var r=W.querySelector('[name=font]:checked');
    return r ? r.value : '';
  }
  function isBlockFont(name){
    var c=W.querySelector('[name=font][value="'+name+'"]');
    return !c || c.closest('.fontchip').dataset.block==='1';
  }


  function syncFonts(){
    // Registration numbers must be plain vertical block characters, so the
    // non-block faces are removed from the grid entirely - an order that
    // cannot legally be placed is not worth showing.
    var lock = isNum() && kind()!=='Both';
    var chips=W.querySelectorAll('.fontchip'), moved=false;
    for(var i=0;i<chips.length;i++){
      var c=chips[i], inp=c.querySelector('input'),
          legal = !lock || c.dataset.block==='1',
          shown = legal;
      inp.disabled=!legal;
      // `off` hides it; an illegal face stays unchecked even if its tab is up
      c.classList.toggle('off', !shown);
      if(!legal && inp.checked){ inp.checked=false; moved=true; }
    }
    // Cleared, not swapped for the first legal face. Picking one for them is
    // how you end up cutting a font nobody chose; the step will not advance
    // until they choose again, and `fonthint` says why theirs went away.
    if(moved && $('e4')) $('e4').textContent =
      'That font is not legal on a registration number - pick another.';
    // Only the mixed case needs explaining: the chosen face lands on the name
    // while the numbers are cut in Block regardless. Everything else is
    // self-evident once the illegal faces are gone.
    var mixed = isNum() && hasName() && !isBlockFont(font());
    $('fonthint').innerHTML = mixed
      ? 'This font goes on the <strong>name</strong>. Your registration numbers are '
        + 'cut in Block either way &mdash; the law requires it.'
      : '';
    // Chips preview the real lettering, not a stand-in.
    // The specimen shows whatever that tab's faces will actually be cut on:
    // the number under Block, the name under Display and Script. Otherwise a
    // script face previews as "IA 3717" while the hint says it goes on the name.
    var num=isNum() && ($('f_text').value.trim() || PLACEHOLDER),
        nm=hasName() && $('f_name2').value.trim();
    var demo=(num || nm) || 'Abc';
    if(demo.length>7) demo=demo.slice(0,7).trim();
    var d=W.querySelectorAll('.fontdemo');
    for(var j=0;j<d.length;j++) d[j].textContent=demo;
  }

  /** Tier-1 check on the registration number. Advisory only. */
  function runValidate(){
    var box=$('vcheck'); if(!box || !window.BNS_VALIDATE) return;
    if(!isNum() || !$('f_text').value.trim()){ box.className='vcheck'; box.innerHTML=''; return; }
    var v=window.BNS_VALIDATE.check($('f_text').value);
    if(v.level==='vok'){
      box.className='vcheck vok';
      box.innerHTML = v.state ? 'Reads as a <strong>'+esc(v.state)+'</strong> number.' : '';
      return;
    }
    box.className='vcheck '+v.level;
    box.innerHTML=v.msg;
  }

  function summary(){
    var rows=[], k=kind();
    var kb=W.querySelector('[name=kind]:checked');
    rows.push([k, '$'+(kb?kb.dataset.base:19)]);
    var h=val('height');
    if(h && +h.dataset.add>0) rows.push([h.value+'" characters','+$'+h.dataset.add]);
    var ups=W.querySelectorAll('[name=upgrade]:checked');
    for(var i=0;i<ups.length;i++)
      rows.push([ups[i].value.split(' - ')[0],'+$'+ups[i].dataset.add]);
    var txt=[];
    if(isNum() && $('f_text').value.trim()) txt.push($('f_text').value.trim());
    if(hasName() && $('f_name2').value.trim()) txt.push($('f_name2').value.trim());
    var c=val('color');
    // One glance: what it says, how it looks, what it costs. Line items are a
    // click away rather than four more rows of height in the hero.
    var box=$('summary');
    var open=box.classList.contains('open');
    box.innerHTML =
      '<div class=sumline><span>'+esc(txt.join('  ·  ')||'Your lettering')+'</span>'+
      '<span class=summeta>'+esc((val('height')||{value:'3'}).value)+'&quot; · '+
      esc(c?c.value:'Black')+' · '+esc(font())+' · free shipping</span></div>'+
      '<div class=sumitems>'+rows.map(function(r){
        return '<div class=sumrow><span>'+esc(r[0])+'</span><b>'+esc(r[1])+'</b></div>';
      }).join('')+'</div>'+
      '<div class="sumrow sumtot"><span>'+
        '<button type=button class=sumtoggle id=sumtog>'+
        (open?'Hide':'Show')+' '+rows.length+' item'+(rows.length===1?'':'s')+
        '</button></span><b>$'+price()+'</b></div>';
    if(open) box.classList.add('open');
    $('sumtog').addEventListener('click',function(){
      box.classList.toggle('open'); summary(); });
  }
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}

  // Null until the first render, so arriving on the page is not a "price went
  // up" event. Only an increase animates - watching the total flash while it
  // drops would read as a penalty.
  var lastTot=null;

  function bumpTotal(){
    var box=tot.parentNode;
    box.classList.remove('bump');
    void box.offsetWidth;   // reflow, or re-adding in the same frame no-ops
    box.classList.add('bump');
  }

  function render(){
    var p=price();
    if(lastTot!==null && p>lastTot) bumpTotal();
    lastTot=p;
    tot.textContent='$'+p;
    if(!isLast()) nextBtn.textContent=nextLabel();
    syncFonts(); syncOutline(); renderPreview();
    if(cur===2){ runValidate(); }
    if(isLast()) summary();
  }

  function show(n){
    // clamp to a step that is actually applicable right now
    cur = ids().indexOf(n)>=0 ? n : ids()[0];
    steps.forEach(function(s){ s.classList.toggle('on', +s.dataset.step===cur); });
    var p=pos(), t=total(), last=isLast();
    fill.style.width=(p/t*100)+'%';
    stepnum.textContent='Step '+p+' of '+t;
    backBtn.hidden = p===1;
    nextBtn.textContent = last ? 'Pay $'+price() : nextLabel();
    nextBtn.classList.toggle('paybtn', last);
    document.getElementById('prevwrap').hidden = last;
    if(cur===2){ runValidate(); }
    if(last){ summary(); initPay(); }
    render();
    var top=W.getBoundingClientRect().top+window.scrollY-80;
    if(window.scrollY>top) window.scrollTo({top:top,behavior:'smooth'});
    // The first text input in DOM order may be the one we just hid (step 2
    // keeps both the number and name fields in the markup), and focusing a
    // display:none element silently does nothing.
    var cands=W.querySelectorAll('.step.on input[type=text],.step.on input[type=email]');
    for(var fi=0; fi<cands.length; fi++){
      if(cands[fi].offsetParent === null) continue;
      if(cur!==1 && window.matchMedia('(min-width:900px)').matches) cands[fi].focus();
      break;
    }
  }

  function validate(){
    if(cur===2){
      if(!$('f_text').value.trim()){
        $('e2').textContent='We need your registration number to cut it.';
        return false; }
      $('e2').textContent=''; return true;
    }
    if(cur===3){
      if(!$('f_name2').value.trim()){
        $('e3').textContent='We need the name to cut it.';
        return false; }
      $('e3').textContent=''; return true;
    }
    if(cur===4){
      if(!font()){
        $('e4').textContent='Pick a font to carry on.';
        return false; }
      $('e4').textContent=''; return true;
    }
    if(isLast()){
      var em=$('f_email').value.trim();
      if(!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(em)){
        $('e5').textContent='We need a valid email for your receipt.';
        $('f_email').focus(); return false; }
      if(!$('f_name').value.trim()){
        $('e5').textContent='We need a name for the order.';
        $('f_name').focus(); return false; }
      $('e5').textContent=''; return true;
    }
    return true;
  }

  function payload(){
    var ups=[];
    W.querySelectorAll('[name=upgrade]:checked').forEach(function(u){ups.push(u.value);});
    return {kind:kind(), text:$('f_text').value.trim(),
            boatname:$('f_name2').value.trim(), state:stateFromPrefix(),
            height:(val('height')||{value:'3'}).value, font:font(),
            color:(val('color')||{value:'Black'}).value, upgrades:ups.join(' | '),
            outline:hasOutline()?1:0,
            outline_color:hasOutline()
              ? (val('outline_color')||{value:'White'}).value : '',
            name:$('f_name').value.trim(), email:$('f_email').value.trim(),
            quoted_total:price(), page:location.pathname};
  }

  // ---- payment ---------------------------------------------------------
  function initPay(){
    if(mounted) return;
    if(!window.BNS_STRIPE_PK || !window.Stripe){
      // The sandbox card field no longer carries a TEST MODE banner, so it is
      // only safe somewhere nobody can mistake it for a real shop. On a real
      // domain with no Stripe keys, fall back to the payment-link flow rather
      // than show a card field that silently takes no payment - a customer
      // would otherwise believe they had paid.
      var h=location.hostname;
      var preview = /(^|\.)workers\.dev$/.test(h) || /(^|\.)pages\.dev$/.test(h)
                 || h==='localhost' || h==='127.0.0.1' || h==='';
      if(window.BNS_PAY_MODE==='sandbox' && preview){ mounted=true; mountSandbox(); }
      else { degrade(); }
      return;
    }
    mounted=true;
    fetch('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({amount:price()})})
      .then(function(r){return r.json();})
      .then(function(j){
        if(!j.clientSecret) throw new Error('no secret');
        clientSecret=j.clientSecret;
        stripe=window.Stripe(window.BNS_STRIPE_PK);
        elements=stripe.elements({clientSecret:clientSecret,
          appearance:{theme:'stripe',variables:{colorPrimary:'#1d7a48',
            colorText:'#12242e',borderRadius:'10px',fontSizeBase:'16px'}}});
        elements.create('payment',{layout:'tabs'}).mount('#payelement');
      })
      .catch(function(){ mounted=false; degrade(); });
  }
  function mountSandbox(){
    $('payelement').classList.add('sandbox');
    $('payelement').innerHTML=window.BNS_MOCKPAY_HTML;
    $('payhint').textContent='';
    window.BNS_MOCKPAY.wire();
    sandbox=true;
  }

  function degrade(){
    // No Stripe keys yet, or the intent failed. Do NOT render a fake card field -
    // collect the order and promise a payment link instead.
    var w=$('paywrap');
    if(w.dataset.degraded) return;
    w.dataset.degraded='1';
    $('payelement').innerHTML='<div class=paysoft><b>No card needed yet.</b>'+
      '<span>Send the order and we will email your proof within 12 hours. '+
      'Once you approve it we send the payment link, and it is cut after '+
      'that \u2014 so nothing is charged for artwork you have not seen.</span></div>';
    $('payhint').textContent='';
    nextBtn.textContent='Send my order';
  }

  function finish(extra){
    var d=payload(); if(extra) for(var k in extra) d[k]=extra[k];
    return fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(d)}).then(function(r){return r.json();});
  }

  function done(j,paid,test){
    // No test marker on screen any more, by request. The protection that
    // matters is in initPay(): the sandbox only mounts on a preview host, so a
    // real customer on a real domain never sees this card field at all. Orders
    // are still flagged test_mode=1 in D1 and [TEST] in the shop email.
    W.innerHTML='<div class=okbox><div class=oktick>&#10003;</div>'+
      '<h2>'+(paid?'Paid &mdash; order ':'Order ')+esc(j.ref||'received')+'</h2>'+
      '<p>'+(paid?'Thanks. ':'')+'A confirmation is on its way to <strong>'+
      esc($('f_email')?$('f_email').value:'your inbox')+'</strong>'+
      ', and your proof follows within 12 hours.</p>'+
      '<p class=hint>We email your proof within 12 hours. Nothing is cut until '+
      'you approve it. Spotted a '+
      'mistake? Email us today with this reference and we can almost always stop '+
      'it before the plotter runs.</p>'+
      '<a class="btn lg" href="/">Back to the shop</a></div>';
    W.scrollIntoView({block:'center'});
  }

  // ---- wiring ----------------------------------------------------------
  nextBtn.addEventListener('click',function(){
    if(!validate()) return;
    if(!isLast()){ show(stepAfter(cur)); return; }
    if(paying) return;
    paying=true; nextBtn.disabled=true; nextBtn.textContent='Working…';

    if(sandbox){
      var card=window.BNS_MOCKPAY.collect();
      if(!card){ paying=false; nextBtn.disabled=false;
                 nextBtn.textContent='Pay $'+price(); return; }
      W.classList.add('paying');
      // Deliberate pause so the demo feels like a real authorisation.
      setTimeout(function(){
        finish({payment:'sandbox', test_mode:1,
                card_brand:card.brand, card_last4:card.last4})
          .then(function(j){
            if(!j.ok) throw new Error(j.error||'failed');
            done(j,true,true);
          })
          .catch(function(){
            W.classList.remove('paying');
            paying=false; nextBtn.disabled=false; nextBtn.textContent='Pay $'+price();
            window.BNS_MOCKPAY.fail('Could not save the test order. Try again.');
          });
      }, 900);
      return;
    }

    if(stripe && clientSecret){
      finish({payment:'stripe'}).then(function(j){
        return stripe.confirmPayment({elements:elements, redirect:'if_required',
          confirmParams:{receipt_email:$('f_email').value.trim()}})
          .then(function(res){
            if(res.error){ throw new Error(res.error.message||'Card declined.'); }
            return fetch('/api/order',{method:'POST',
              headers:{'Content-Type':'application/json'},
              body:JSON.stringify(Object.assign(payload(),
                {paid:1, ref:j.ref, payment:'stripe-confirmed'}))})
              .then(function(){ done(j,true); });
          });
      }).catch(function(err){
        paying=false; nextBtn.disabled=false; nextBtn.textContent='Pay $'+price();
        $('e5').textContent=(err&&err.message)||'That card did not go through.';
      });
    } else {
      finish({payment:'payment-link'}).then(function(j){
        if(!j.ok) throw new Error();
        done(j,false);
      }).catch(function(){
        paying=false; nextBtn.disabled=false; nextBtn.textContent='Send my order';
        $('e5').innerHTML='That did not go through. Email '+
          '<a href="mailto:orders@numbermyboat.com">orders@numbermyboat.com</a>'+
          ' and we will pick it up by hand.';
      });
    }
  });
  backBtn.addEventListener('click',function(){ show(stepBefore(cur)); });

  // Step 1 auto-advances: one tap, no Continue. Biggest single fatigue win.
  W.querySelectorAll('[name=kind]').forEach(function(r){
    r.addEventListener('change',function(){ render();
      setTimeout(function(){ show(stepAfter(1)); },140); });
  });

  W.addEventListener('input',render);
  W.addEventListener('change',render);
  W.addEventListener('keydown',function(ev){
    if(ev.key==='Enter' && ev.target.tagName==='INPUT'){ ev.preventDefault(); nextBtn.click(); }
  });

  // If Stripe.js never loads (blocked, offline), degrade rather than hang.
  setTimeout(function(){ if(isLast() && !mounted) degrade(); },4000);
  // ---- the phone app layer ----------------------------------------------
  // A full-screen card deck over the page - the whole phone experience, not
  // a hero element. The page underneath is untouched and in normal flow, so
  // dismissing this drops you straight onto it.
  var track=$('apptrack'), prog=$('appprog'), shell=$('appshell');
  if(track && prog && shell){
    var segs=[].slice.call(prog.querySelectorAll('.appbar-seg'));
    var appMq=matchMedia('(max-width:760px)');
    function phone(){ return appMq.matches; }

    function markSeg(i){
      for(var d=0;d<segs.length;d++) segs[d].classList.toggle('on', d===i);
    }
    function current(){
      // Nearest card centre to the track's centre. Measured off
      // getBoundingClientRect, NOT offsetLeft: offsetLeft is relative to the
      // nearest POSITIONED ancestor, so the centres would come out in the
      // wrong coordinate space and the progress bar would never move.
      var tr=track.getBoundingClientRect(), mid=tr.left + tr.width/2,
          best=0, gap=1e9;
      for(var i=0;i<track.children.length;i++){
        var r=track.children[i].getBoundingClientRect(),
            g=Math.abs((r.left + r.width/2) - mid);
        if(g<gap){ gap=g; best=i; }
      }
      return best;
    }
    function load(card){
      if(!card || card.dataset.loaded) return;
      card.dataset.loaded='1';
      var n=card.querySelectorAll('[data-src],[data-srcset]');
      for(var i=0;i<n.length;i++){
        var el=n[i];
        if(el.dataset.srcset){ el.srcset=el.dataset.srcset; el.removeAttribute('data-srcset'); }
        if(el.dataset.src){ el.src=el.dataset.src; el.removeAttribute('data-src'); }
      }
      card.classList.remove('pending');
    }
    function loadAround(i){
      load(track.children[i]); load(track.children[i-1]); load(track.children[i+1]);
    }
    function goTo(i){
      var c=track.children[i]; if(!c) return;
      var tr=track.getBoundingClientRect(), r=c.getBoundingClientRect();
      // Smooth scrolling runs on animation frames, which do not tick while
      // the tab is hidden, and a reader who asked for reduced motion should
      // not be given an animation.
      var still = document.hidden
               || matchMedia('(prefers-reduced-motion: reduce)').matches;
      track.scrollTo({left: track.scrollLeft + (r.left - tr.left),
                      behavior: still ? 'auto' : 'smooth'});
      loadAround(i);
    }

    // Straight from the scroll event, with no requestAnimationFrame in front
    // of it: rAF does not fire while the tab is hidden, so a scroll landing
    // in a backgrounded tab would leave a pending flag set and freeze the
    // progress bar for the rest of the session.
    track.addEventListener('scroll', function(){
      var i=current(); markSeg(i); loadAround(i);
    }, {passive:true});

    // Tap the left or right edge to move a card, the way a stories UI does.
    track.addEventListener('click', function(ev){
      if(ev.target.closest('a,button')) return;
      var r=track.getBoundingClientRect(), x=ev.clientX - r.left, i=current();
      if(x < r.width*0.28) goTo(Math.max(0, i-1));
      else if(x > r.width*0.72) goTo(Math.min(track.children.length-1, i+1));
    });

    function openApp(){
      if(!phone() || shell.dataset.open) return;
      shell.dataset.open='1';
      shell.hidden=false;
      document.body.classList.add('appon');
      loadAround(0);
    }
    function closeApp(){
      if(!shell.dataset.open) return;
      delete shell.dataset.open;
      shell.hidden=true;
      document.body.classList.remove('appon');
      try{ sessionStorage.setItem('bnsAppSeen','1'); }catch(e){}
    }
    $('appskip').addEventListener('click', closeApp);
    addEventListener('keydown', function(ev){
      if(ev.key==='Escape' && shell.dataset.open) closeApp();
    });
    // Rotating past the breakpoint would otherwise leave the body locked with
    // the layer's styles gone.
    if(appMq.addEventListener)
      appMq.addEventListener('change', function(){ if(!phone()) closeApp(); });

    // Shown once per visit. Coming back to a second page and being handed the
    // deck again, after you already chose to browse, is hostile.
    var seen=false;
    try{ seen=sessionStorage.getItem('bnsAppSeen')==='1'; }catch(e){}
    if(!seen) openApp();
  }

  // ---- the phone order sheet --------------------------------------------
  // Every "Start your order" on a page that already carries the wizard opens
  // that wizard full screen instead of navigating to /design/ - same element,
  // same state, no second copy of the form. Pages without a hero wizard
  // (/pricing/, the guides) have no .heroF, so their links navigate as before.
  var sheet=document.querySelector('.heroF');
  if(sheet && sheet.contains(W)){
    var opener=null;

    function sheetOpen(){ return document.body.classList.contains('sheeton'); }

    function openSheet(from){
      if(sheetOpen()) return;
      opener=from||null;
      document.body.classList.add('sheeton');
      sheet.setAttribute('aria-modal','true');
      sheet.scrollTop=0;
      // The panel just went from a 343px column to the full viewport, and the
      // boat preview sizes its lettering off the panel's width.
      dispatchEvent(new Event('resize'));
      var x=sheet.querySelector('.sheetx'); if(x) x.focus();
      // Back should close the sheet, not leave the page - on a phone that is
      // what the gesture means.
      try{ history.pushState({bnsSheet:1}, ''); }catch(e){}
    }

    function closeSheet(pop){
      if(!sheetOpen()) return;
      document.body.classList.remove('sheeton');
      sheet.setAttribute('aria-modal','false');
      if(opener && opener.focus) opener.focus();
      opener=null;
      if(!pop){ try{ if(history.state && history.state.bnsSheet) history.back(); }
                catch(e){} }
    }

    // Anything pointing at the order page, plus the hero card's own button.
    document.addEventListener('click', function(ev){
      var t=ev.target.closest('a[href="/design/"], .sheetgo, .sheetx');
      if(!t) return;
      if(t.classList.contains('sheetx')){ ev.preventDefault(); closeSheet(); return; }
      // Desktop keeps the wizard inline, so the links stay links.
      if(!matchMedia('(max-width:760px)').matches) return;
      ev.preventDefault();
      openSheet(t);
    });
    addEventListener('keydown', function(ev){
      if(ev.key==='Escape' && sheetOpen()) closeSheet();
    });
    addEventListener('popstate', function(){ closeSheet(true); });
    // Watch the breakpoint itself rather than piggybacking on resize: this
    // fires exactly when the query flips, however it was crossed. Rotating to
    // landscape past it would otherwise leave the body scroll-locked and
    // .heroF still aria-modal, with every sheet style gone.
    var mq=matchMedia('(max-width:760px)');
    function onBreak(){ if(sheetOpen() && !mq.matches) closeSheet(); }
    if(mq.addEventListener) mq.addEventListener('change', onBreak);
    else if(mq.addListener) mq.addListener(onBreak);   // Safari < 14
  }

  seedStatePrefix();
  syncOutline();   // hide the outline row before first paint
  // The server renders White checked as a sensible default. Without this it
  // looks like a deliberate customer choice, so syncOutline() bails out and
  // never corrects it - pick a white fill and you get a white outline on
  // white letters, which is nothing at all.
  (function(){
    var d=W.querySelector('[name=outline_color]:checked');
    if(d) d.dataset.auto='1';
  })();
  W.querySelectorAll('[name=outline_color]').forEach(function(r){
    r.addEventListener('click', function(){ r.dataset.auto='0'; });
  });

  // /design/?name=Wet+Couch&port=Evansdale%2C+IA - the name generator's CTA.
  // Without this the name is dropped and the customer retypes what they just
  // picked, which is the fastest way to lose them.
  (function(){
    var q=new URLSearchParams(location.search);
    var nm=(q.get('name')||'').slice(0,40).trim();
    if(!nm) return;
    var kindEl=[].slice.call(W.querySelectorAll('[name=kind]'))
      .filter(function(r){return r.value==='Boat name';})[0];
    if(kindEl) kindEl.checked=true;
    var f=$('f_name2'); if(f) f.value=nm;
    render();
    show(2);
    return true;
  })() || show(1);
})();
"""
