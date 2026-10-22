# -*- coding: utf-8 -*-
"""The order wizard - this site's only conversion element.

Five steps, one decision each, in a fixed-height shell so the page never jumps:

  1. What do you need?      three cards, auto-advances on click (no typing)
  2. What should it say?    the only step that demands real typing
  3. How should it look?    clicks only; live preview flips its hull colour so
                            light vinyl always renders on dark and vice versa
  4. Anything else?         merchandising - where AOV is actually made
  5. Checkout               Stripe Payment Element, embedded

Anti-fatigue rules this file holds to:
  - never more than one required text field per step
  - steps 1, 3 and 4 are pure clicking
  - name/phone/boat/notes are optional or collapsed; the card supplies the name
  - the running total is visible from step 1 so the price is never a late surprise

Price is computed here for instant feedback and RE-COMPUTED in worker/index.js,
which is the authority. Never trust a posted total.
"""
from content import (PRICE, FONTS, COLORS, POPULAR_COLORS, STATES, UPGRADES)
import hull as H

HEIGHTS = [(3, 0, "3&quot;", "legal minimum"), (4, 4, "4&quot;", "reads better"),
           (5, 8, "5&quot;", "bold"), (6, 13, "6&quot;", "big transom")]

# (label, base, caption, price, flag, key) - caption is one short line; the
# thumbnail carries the explanation.
KINDS = [
    ("Registration numbers", 19, "On the bow, both sides", "$19", "", "numbers"),
    ("Boat name", 29, "On the transom", "from $29", "", "name"),
    ("Both", 44, "Bow and transom", "from $44", "Save $4", "both"),
]

def _thumb(key):
    """Miniature of the hull showing where this option's lettering sits."""
    body = ('<path d="M3 11 C15 8 46 7 105 8 L104 25 C104 29 101 31 97 31 '
            'L24 31 C15 31 8 23 4 15 Z" fill="#dfeaf1" stroke="#b9ccd8" stroke-width="1"/>')
    num = '<rect x="16" y="16" width="34" height="7" rx="1.5" fill="#15516f"/>'
    nm  = '<rect x="66" y="16" width="30" height="7" rx="1.5" fill="#15516f"/>'
    nm2 = '<rect x="44" y="16" width="52" height="8" rx="1.5" fill="#15516f"/>'
    inner = {"numbers": num, "name": nm2, "both": num + nm}[key]
    return ('<svg class=kthumb viewBox="0 0 110 36" aria-hidden="true">%s%s</svg>'
            % (body, inner))


def _colors(prefix):
    pop = [c for c in COLORS if c[0] in POPULAR_COLORS]
    rest = [c for c in COLORS if c[0] not in POPULAR_COLORS]
    def sw(c, checked=False):
        name, hexv, light = c
        return ('<label class=csw title="%s"><input type=radio name="%s" value="%s" '
                'data-hex="%s" data-light="%d"%s>'
                '<span style="background:%s"></span><em>%s</em></label>'
                % (name, prefix, name, hexv, light,
                   " checked" if checked else "", hexv, name))
    return ("".join(sw(c, c[0] == "Black") for c in pop),
            "".join(sw(c) for c in rest))


def form():
    states = "".join('<option value="%s">%s</option>' % (s["name"], s["name"])
                     for s in STATES)
    fonts_block = "".join('<option value="%s">%s</option>' % (f, f)
                          for f in FONTS if "Script" not in f and
                          f not in ("Great Vibes", "Lobster", "Old English"))
    fonts_all = "".join('<option value="%s">%s</option>' % (f, f) for f in FONTS)
    heights = "".join(
        '<label class=opt><input type=radio name=height value="%d" data-add="%d"%s>'
        '<span>%s<em>%s</em></span></label>'
        % (h, add, " checked" if h == 3 else "", lbl,
           note if add == 0 else note + " &middot; +$%d" % add)
        for h, add, lbl, note in HEIGHTS)
    kinds = "".join(
        '<label class=kind><input type=radio name=kind value="%s" data-base="%d"%s>'
        '<span class=kindbox>%s%s<b>%s</b><em>%s</em><i>%s</i></span></label>'
        % (lbl, base, " checked" if key == "numbers" else "",
           '<span class=flag>%s</span>' % flag if flag else "",
           _thumb(key), lbl, blurb, price)
        for lbl, base, blurb, price, flag, key in KINDS)
    ups = "".join(
        '<label class=mcard><input type=checkbox name=upgrade value="%s" data-add="%d">'
        '<span class=mbox>%s<b>%s</b><em>%s</em><i>%s</i>'
        '<span class=mamt>+$%d</span><span class=mtick aria-hidden="true">&#10003;</span>'
        '</span></label>'
        % (lbl, amt, '<span class=flag>%s</span>' % flag if flag else "",
           lbl.split(" - ")[0], blurb, note, amt)
        for lbl, amt, blurb, flag, note in UPGRADES)
    pop, rest = _colors("color")

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
    <p class=tinylink>Motor decals, carpet logos or striping?
      <a href="/contact/">Ask us</a>.</p>
  </section>

  <!-- 2 ------------------------------------------------------------- -->
  <section class=step data-step="2">
    <h2 id=s2h>What should it say?</h2>
    <p class=sublede id=s2sub>Copy it off your registration card, spaces and all.</p>
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
    <div id=statewrap style="margin-top:14px">
      <label for=f_state>Your state</label>
      <select id=f_state name=state>
        <option value="">Select your state&hellip;</option>""" + states + """
        <option value="Other">Other / not listed</option>
        <option value="USCG documented">USCG documented vessel</option></select>
      <div class=hint id=statehint>We check your prefix and spacing before it cuts.</div>
    </div>
    <div class=err id=e2 role=alert></div>
  </section>

  <!-- 3 ------------------------------------------------------------- -->
  <section class=step data-step="3">
    <h2>How should it look?</h2>
    
    <fieldset><legend>Colour</legend>
      <div class=swrow>""" + pop + """</div>
      <details class=morecol><summary>14 more colours</summary>
        <div class=swrow style="margin-top:9px">""" + rest + """</div></details>
    </fieldset>
    <fieldset><legend>Character height</legend>
      <div class=opts>""" + heights + """</div>
    </fieldset>
    <fieldset style="margin-bottom:2px"><legend>Font</legend>
      <select id=f_font name=font data-block='""" + fonts_block + """'
              data-all='""" + fonts_all + """'>""" + fonts_block + """</select>
      <div class=hint id=fonthint>Numbers must be block characters by law, so
        script is not offered.</div>
    </fieldset>
  </section>

  <!-- 4 ------------------------------------------------------------- -->
  <section class=step data-step="4">
    <h2>Anything else?</h2>
    <p class=sublede>Shipping is already paid &mdash; these add nothing to send.</p>
    <div class=mgrid>""" + ups + """</div>
    <p class=tinylink><a href="#" id=skipups>Skip &mdash; none of these</a></p>
  </section>

  <!-- 5 ------------------------------------------------------------- -->
  <section class=step data-step="5">
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
    <details class=extra><summary>Add a phone, boat details or a note</summary>
      <div class="fieldrow two" style="margin-top:11px">
        <div><label for=f_phone>Phone</label>
          <input type=tel id=f_phone name=phone autocomplete=tel></div>
        <div><label for=f_boat>Boat make &amp; model</label>
          <input type=text id=f_boat name=boat placeholder="2004 Tracker Pro 170"></div>
      </div>
      <div style="margin-top:11px"><label for=f_notes>Notes</label>
        <textarea id=f_notes name=notes rows=2
          placeholder="Dark blue hull. Rivets across the panel."></textarea></div>
    </details>
    <div class=err id=e5 role=alert></div>
    <p class=guar>Proof before we cut &middot; free re-cut &middot; full refund if
      you do not like the proof</p>
  </section>

  </div>

  <div class=wizfoot>
    <button type=button class="btn lg" id=next>Continue</button>
    <p class=foothint id=foothint>Free shipping &middot; ships next business day</p>
  </div>
</div>""").replace("__HULL__", H.SVG)


def color_js():
    return ("window.BNS_COL={%s};" %
            ",".join('"%s":["%s",%d]' % (n, h, l) for n, h, l in COLORS))


JS = r"""
(function(){
  var W=document.getElementById('order'); if(!W) return;
  var COL=window.BNS_COL||{};
  var steps=[].slice.call(W.querySelectorAll('.step'));
  var cur=1, MAX=steps.length;
  var $=function(id){return document.getElementById(id);};
  var nextBtn=$('next'), backBtn=$('back'), fill=$('wizfill'),
      stepnum=$('stepnum'), tot=$('total'), foothint=$('foothint');
  var stripe=null, elements=null, clientSecret=null, mounted=false,
      paying=false, sandbox=false;

  function kind(){var r=W.querySelector('[name=kind]:checked');return r?r.value:'Registration numbers';}
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

  var SCRIPTY=/script|vibes|lobster|old english/i;
  function renderPreview(){
    var lbl=$('prevlbl'); if(!lbl || !window.BNS_HULL) return;
    var c=val('color'), cname=c?c.value:'Black';
    var meta=COL[cname]||['#111111',0];
    var h=val('height'), hv=h?h.value:'3';
    var fn=$('f_font').value||'Block';
    window.BNS_HULL.render({
      hex: meta[0], light: !!meta[1], font: fn,
      showNum: isNum(), showName: hasName(),
      number: ($('f_text').value||'').trim(),
      name: ($('f_name2').value||'').trim()
    });
    lbl.innerHTML = '<b>'+hv+'&quot;</b> '+esc(fn.replace(/ \(.*\)/,''))+
      ' &middot; <b>'+esc(cname)+'</b> &middot; '+
      (isNum() ? (hasName()? 'pair + name, pre-spaced' : 'one pair, pre-spaced')
               : 'one decal, pre-spaced');
  }

  function syncFonts(){
    var sel=$('f_font'), lock=isNum() && kind()!=='Both';
    var want = lock ? sel.dataset.block : sel.dataset.all;
    if(sel.dataset.state !== (lock?'b':'a')){
      var keep=sel.value;
      sel.innerHTML=want; sel.dataset.state=(lock?'b':'a');
      var ok=[].slice.call(sel.options).some(function(o){return o.value===keep;});
      sel.value = ok ? keep : sel.options[0].value;
    }
    $('fonthint').textContent = lock
      ? 'Registration numbers must be plain vertical block characters, so script fonts are not offered.'
      : 'Script reads beautifully on a transom. Any registration numbers in this order stay block.';
  }

  function syncStep2(){
    var num=isNum(), nm=hasName();
    $('numwrap').hidden=!num; $('namewrap').hidden=!nm;
    $('statewrap').hidden=!num;
    $('s2h').textContent = num&&nm ? 'What should they say?'
                         : num ? 'What is your registration number?'
                               : 'What is the boat called?';
    $('s2sub').textContent = num
      ? 'Copy it straight off your registration card, spaces and all.'
      : 'We cut it exactly as typed, so capitals matter.';
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
      esc(c?c.value:'Black')+' · '+esc($('f_font').value)+' · free shipping</span></div>'+
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
    if(cur===5) summary();
  }

  function show(n){
    cur=Math.max(1,Math.min(MAX,n));
    steps.forEach(function(s){ s.classList.toggle('on', +s.dataset.step===cur); });
    fill.style.width=(cur/MAX*100)+'%';
    stepnum.textContent='Step '+cur+' of '+MAX;
    backBtn.hidden = cur===1;
    nextBtn.textContent = cur===MAX ? 'Pay $'+price() : 'Continue';
    nextBtn.classList.toggle('paybtn', cur===MAX);
    foothint.textContent = cur===MAX
      ? 'Free shipping · proof before we cut · full refund if you do not like it'
      : 'Free shipping · ships next business day';
    document.getElementById('prevwrap').hidden = (cur===5);
    if(cur===2) syncStep2();
    if(cur===5){ summary(); initPay(); }
    render();
    var top=W.getBoundingClientRect().top+window.scrollY-80;
    if(window.scrollY>top) window.scrollTo({top:top,behavior:'smooth'});
    var f=W.querySelector('.step.on input[type=text],.step.on input[type=email]');
    if(f && cur!==1 && window.matchMedia('(min-width:900px)').matches) f.focus();
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
    if(cur===5){
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
            boatname:$('f_name2').value.trim(), state:$('f_state').value,
            height:(val('height')||{value:'3'}).value, font:$('f_font').value,
            color:(val('color')||{value:'Black'}).value, upgrades:ups.join(' | '),
            name:$('f_name').value.trim(), email:$('f_email').value.trim(),
            phone:$('f_phone').value.trim(), boat:$('f_boat').value.trim(),
            notes:$('f_notes').value.trim(), quoted_total:price(),
            page:location.pathname};
  }

  // ---- payment ---------------------------------------------------------
  function initPay(){
    if(mounted) return;
    if(!window.BNS_STRIPE_PK || !window.Stripe){
      if(window.BNS_PAY_MODE==='sandbox'){ mounted=true; mountSandbox(); }
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
  var skip=$('skipups');
  if(skip) skip.addEventListener('click',function(ev){ev.preventDefault();show(5);});

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
