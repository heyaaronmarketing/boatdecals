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
from content import (PRICE, FONTS, COLORS, ORDER_COLORS, STATES, UPGRADES)
import preview as PV

HEIGHTS = [(3, 0, "3&quot;", "legal minimum"), (4, 4, "4&quot;", "reads better"),
           (5, 8, "5&quot;", "bold"), (6, 13, "6&quot;", "big transom")]

# (label, base, caption, price, flag, key) - caption is one short line; the
# thumbnail carries the explanation.
KINDS = [
    ("Registration numbers", 19, "On the bow, both sides", "$19", "", "numbers"),
    ("Boat name", 29, "On the transom", "from $29", "", "name"),
    ("Both", 44, "Bow and transom", "from $44", "Save $4", "both"),
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


def _colors(prefix):
    """Two colours, named rather than left as unlabelled swatches - at this
    size a white chip and a light-grey chip are hard to tell apart."""
    picks = [c for c in COLORS if c[0] in ORDER_COLORS]
    picks.sort(key=lambda c: ORDER_COLORS.index(c[0]))
    return "".join(
        '<label class=csw><input type=radio name="%s" value="%s" data-hex="%s" '
        'data-light="%d"%s><span class=cswbox><i style="background:%s"></i>%s</span>'
        '</label>'
        % (prefix, name, hexv, light, " checked" if name == "Black" else "",
           hexv, name)
        for name, hexv, light in picks)


def form():
    # Each chip renders the customer's own lettering in that face, so the
    # choice is made on the thing itself rather than on a font name.
    fonts = "".join(
        '<label class=fontchip data-block="%d"><input type=radio name=font value="%s"%s>'
        '<span class=fontbox><span class=fontdemo style="font-family:%s">%s</span>'
        '<em>%s</em></span></label>'
        % (1 if block else 0, lbl, " checked" if i == 0 else "",
           css.replace('"', "&quot;"), "Abc", lbl)
        for i, (lbl, css, _g, block) in enumerate(FONTS))
    heights = "".join(
        '<label class=opt><input type=radio name=height value="%d" data-add="%d"%s>'
        '<span class=optbox>%s</span>'
        '<em class=optcap>%s<b>%s</b></em></label>'
        % (h, add, " checked" if h == 3 else "", lbl, note,
           "included" if add == 0 else "+$%d" % add)
        for h, add, lbl, note in HEIGHTS)
    kinds = "".join(
        '<label class=kind><input type=radio name=kind value="%s" data-base="%d"%s>'
        '<span class=kindbox>%s%s<b>%s</b><em>%s</em><i>%s</i></span></label>'
        % (lbl, base, " checked" if key == "numbers" else "",
           '<span class=flag>%s</span>' % flag if flag else "",
           _thumb(key), lbl, blurb, price)
        for lbl, base, blurb, price, flag, key in KINDS)
    cols = _colors("color")

    return ("""
<div id=order class="panel wiz">
  <div class=wizhead>
    <div class=wizbar><i id=wizfill></i></div>
    <div class=wizmeta>
      <button type=button class=wizback id=back hidden>&larr; Back</button>
      <span id=stepnum>Step 1 of 5</span>
      <span class=wiztot>Total <b id=total>$19</b></span>
    </div>
  </div>

  <div class=prevwrap id=prevwrap>
    <div class=prev id=prev aria-live=polite>__HULL__</div>
    <div class=prevlbl id=prevlbl></div>
  </div>

  <div class=wizbody>

  <!-- 1 ------------------------------------------------------------- -->
  <section class="step on" data-step="1">
    <h2>What do you need?</h2>
    
    <div class=kinds>""" + kinds + """</div>
  </section>

  <!-- 2 ------------------------------------------------------------- -->
  <section class=step data-step="2">
    <h2 class=vh id=s2h>What should it say?</h2>
    <div id=numwrap>
      <label for=f_text>Registration number</label>
      <input type=text id=f_text name=text value="" placeholder="IA 3717 ZW"
             autocomplete=off maxlength=40 autocapitalize=characters spellcheck=false>
    </div>
    <div id=namewrap hidden style="margin-top:14px">
      <label for=f_name2>Boat name</label>
      <input type=text id=f_name2 name=boatname value="" placeholder="Second Wind"
             autocomplete=off maxlength=40 spellcheck=false>
      <div class=hint>Stuck? <a href="/tools/boat-name-generator/" target="_blank"
        rel="noopener">1,000 name ideas</a>.</div>
    </div>
    <div class=err id=e2 role=alert></div>
    <fieldset class=fontset style="margin-top:14px">
      <legend>Pick a font</legend>
      <div class=fontgrid>""" + fonts + """</div>
      <div class=hint id=fonthint></div>
    </fieldset>
  </section>

  <!-- 3 ------------------------------------------------------------- -->
  <section class=step data-step="3">
    <h2>How should it look?</h2>
    
    <fieldset><legend>Colour</legend>
      <div class=swrow>""" + cols + """</div>
      <div class=hint>White on a dark hull, black on a light one &mdash; the law
        wants contrast. Other colours are available,
        <a href="/contact/">just ask</a>.</div>
    </fieldset>
    <fieldset><legend>Character height</legend>
      <div class=opts>""" + heights + """</div>
    </fieldset>
  </section>


  <!-- 4 ------------------------------------------------------------- -->
  <section class=step data-step="4">
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
</div>""").replace("__HULL__", PV.SVG)


def color_js():
    cols = ",".join('"%s":["%s",%d]' % (n, h, l) for n, h, l in COLORS)
    prefixes = ",".join('"%s":"%s"' % (st["ab"], st["name"]) for st in STATES)
    fontcss = ",".join('"%s":"%s"' % (lbl, css.replace('"', "'"))
                       for lbl, css, _g, _b in FONTS)
    return ("window.BNS_COL={%s};window.BNS_PREFIX={%s};window.BNS_FONTCSS={%s};"
            % (cols, prefixes, fontcss))


JS = r"""
(function(){
  var W=document.getElementById('order'); if(!W) return;
  var COL=window.BNS_COL||{};
  var steps=[].slice.call(W.querySelectorAll('.step'));
  var cur=1, MAX=steps.length;
  var $=function(id){return document.getElementById(id);};
  var nextBtn=$('next'), backBtn=$('back'), fill=$('wizfill'),
      stepnum=$('stepnum'), tot=$('total');
  var stripe=null, elements=null, clientSecret=null, mounted=false,
      paying=false, sandbox=false;

  function kind(){var r=W.querySelector('[name=kind]:checked');return r?r.value:'Registration numbers';}

  /** The registration number carries its own state prefix, so asking for the
   *  state again was a field for data we already had. CF=California,
   *  WN=Washington, otherwise the two-letter postal code. */
  function stateFromPrefix(){
    var m=($('f_text').value||'').trim().toUpperCase().match(/^([A-Z]{2})/);
    return (m && (window.BNS_PREFIX||{})[m[1]]) || '';
  }
  function isNum(){return kind()!=='Boat name';}
  function hasName(){return kind()!=='Registration numbers';}
  function val(n){var el=W.querySelector('[name='+n+']:checked');return el||null;}

  function price(){
    var k=W.querySelector('[name=kind]:checked');
    var n=k?parseFloat(k.dataset.base):19;
    var h=val('height'); if(h) n+=parseFloat(h.dataset.add||0);
    var ups=W.querySelectorAll('[name=upgrade]:checked');
    for(var i=0;i<ups.length;i++) n+=parseFloat(ups[i].dataset.add||0);
    return Math.round(n);
  }

  function renderPreview(){
    var lbl=$('prevlbl'); if(!lbl || !window.BNS_PREVIEW) return;
    var c=val('color'), cname=c?c.value:'Black';
    var meta=COL[cname]||['#111111',0];
    var h=val('height'), hv=h?h.value:'3';
    var fn=font();
    window.BNS_PREVIEW.render({
      hex: meta[0], light: !!meta[1], font: fn,
      css: (window.BNS_FONTCSS||{})[fn] || '',
      numBlock: isNum() && hasName() && !isBlockFont(fn),
      showNum: isNum(), showName: hasName(),
      number: ($('f_text').value||'').trim(),
      name: ($('f_name2').value||'').trim()
    });
    lbl.innerHTML = '<b>'+hv+'&quot;</b> '+esc(fn)+
      ' &middot; <b>'+esc(cname)+'</b> &middot; '+
      (isNum() ? (hasName()? 'pair + name, pre-spaced' : 'one pair, pre-spaced')
               : 'one decal, pre-spaced');
  }

  function font(){
    var r=W.querySelector('[name=font]:checked');
    return r ? r.value : 'Block';
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
          ok = !lock || c.dataset.block==='1';
      inp.disabled=!ok;
      c.classList.toggle('off', !ok);
      if(!ok && inp.checked){ inp.checked=false; moved=true; }
    }
    if(moved){
      var first=W.querySelector('.fontchip:not(.off) input');
      if(first) first.checked=true;
    }
    // Only the mixed case needs explaining: the chosen face lands on the name
    // while the numbers are cut in Block regardless. Everything else is
    // self-evident once the illegal faces are gone.
    var mixed = isNum() && hasName() && !isBlockFont(font());
    $('fonthint').innerHTML = mixed
      ? 'This font goes on the <strong>name</strong>. Your registration numbers are '
        + 'cut in Block either way &mdash; the law requires it.'
      : '';
    // Chips preview the real lettering, not a stand-in.
    var demo=(isNum()? $('f_text').value : $('f_name2').value).trim() || 'Abc';
    if(demo.length>7) demo=demo.slice(0,7).trim();
    var d=W.querySelectorAll('.fontdemo');
    for(var j=0;j<d.length;j++) d[j].textContent=demo;
  }

  function syncStep2(){
    var num=isNum(), nm=hasName();
    $('numwrap').hidden=!num; $('namewrap').hidden=!nm;
    $('s2h').textContent = num&&nm ? 'What should they say?'
                         : num ? 'What is your registration number?'
                               : 'What is the boat called?';
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

  function render(){
    tot.textContent='$'+price();
    syncFonts(); renderPreview();
    if(cur===2) syncStep2();
    if(cur===MAX) summary();
  }

  function show(n){
    cur=Math.max(1,Math.min(MAX,n));
    steps.forEach(function(s){ s.classList.toggle('on', +s.dataset.step===cur); });
    fill.style.width=(cur/MAX*100)+'%';
    stepnum.textContent='Step '+cur+' of '+MAX;
    backBtn.hidden = cur===1;
    nextBtn.textContent = cur===MAX ? 'Pay $'+price() : 'Continue';
    nextBtn.classList.toggle('paybtn', cur===MAX);
    document.getElementById('prevwrap').hidden = (cur===MAX);
    if(cur===2) syncStep2();
    if(cur===MAX){ summary(); initPay(); }
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
      var bad=[];
      if(isNum() && !$('f_text').value.trim()) bad.push('your registration number');
      if(hasName() && !$('f_name2').value.trim()) bad.push('your boat name');
      if(bad.length){ $('e2').textContent='We need '+bad.join(' and ')+' to cut it.';
        return false; }
      $('e2').textContent=''; return true;
    }
    if(cur===MAX){
      var em=$('f_email').value.trim();
      if(!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(em)){
        $('e5').textContent='We need a valid email to send your proof.';
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
    $('payelement').innerHTML='<div class=paysoft><b>Card payment is being switched on.</b>'+
      '<span>Send the order now and we will email your proof with a secure payment '+
      'link. Nothing is cut until you approve the proof.</span></div>';
    $('payhint').textContent='';
    nextBtn.textContent='Send my order';
  }

  function finish(extra){
    var d=payload(); if(extra) for(var k in extra) d[k]=extra[k];
    return fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(d)}).then(function(r){return r.json();});
  }

  function done(j,paid,test){
    W.innerHTML='<div class=okbox><div class=oktick>&#10003;</div>'+
      (test?'<div class=testbar style="text-align:left"><b>Test mode</b>'+
            '<span>No payment was taken and no card was stored. This order is '+
            'flagged as a test.</span></div>':'')+
      '<h2>'+(paid?'Paid &mdash; order ':'Order ')+esc(j.ref||'received')+'</h2>'+
      '<p>'+(paid?'Thanks. ':'')+'We are drawing your proof now. It lands in <strong>'+
      esc($('f_email')?$('f_email').value:'your inbox')+'</strong> shortly'+
      (paid?'.':', with a secure payment link.')+'</p>'+
      '<p class=hint>Nothing gets cut until you reply <em>approved</em>. If the proof '+
      'is wrong we redraw it free'+(paid?', or refund you in full':'')+'.</p>'+
      '<a class="btn lg" href="/">Back to the shop</a></div>';
    W.scrollIntoView({block:'center'});
  }

  // ---- wiring ----------------------------------------------------------
  nextBtn.addEventListener('click',function(){
    if(!validate()) return;
    if(cur<MAX){ show(cur+1); return; }
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
      finish({payment:'proof-then-link'}).then(function(j){
        if(!j.ok) throw new Error();
        done(j,false);
      }).catch(function(){
        paying=false; nextBtn.disabled=false; nextBtn.textContent='Send my order';
        $('e5').innerHTML='That did not go through. Email '+
          '<a href="mailto:orders@boatnumbershop.com">orders@boatnumbershop.com</a>'+
          ' and we will pick it up by hand.';
      });
    }
  });
  backBtn.addEventListener('click',function(){ show(cur-1); });

  // Step 1 auto-advances: one tap, no Continue. Biggest single fatigue win.
  W.querySelectorAll('[name=kind]').forEach(function(r){
    r.addEventListener('change',function(){ render(); setTimeout(function(){show(2);},140); });
  });

  W.addEventListener('input',render);
  W.addEventListener('change',render);
  W.addEventListener('keydown',function(ev){
    if(ev.key==='Enter' && ev.target.tagName==='INPUT'){ ev.preventDefault(); nextBtn.click(); }
  });

  // If Stripe.js never loads (blocked, offline), degrade rather than hang.
  setTimeout(function(){ if(cur===5 && !mounted) degrade(); },4000);
  show(1);
})();
"""
