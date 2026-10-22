# -*- coding: utf-8 -*-
"""The order configurator - this site's single conversion element.

Lives on every page as the primary CTA target and is embedded inline on /design/.
Price is computed client-side for instant feedback and RE-COMPUTED server-side in
worker/index.js, which is the authority. Never trust the posted total.
"""
from content import PRICE, FONTS, COLORS, STATES

HEIGHTS = [(3, 0, "3&quot; - the legal minimum"), (4, 4, "4&quot;"),
           (5, 8, "5&quot;"), (6, 13, "6&quot;")]

def options_html():
    st = "".join('<option value="%s">%s</option>' % (s["name"], s["name"]) for s in STATES)
    fo = "".join('<option value="%s">%s</option>' % (f, f) for f in FONTS)
    co = "".join('<option value="%s">%s</option>' % (c[0], c[0]) for c in COLORS)
    hi = "".join(
        '<label class=opt><input type=radio name=height value="%d" data-add="%d"%s>'
        '<span>%s<em>%s</em></span></label>'
        % (h, add, " checked" if h == 3 else "", lbl,
           "included" if add == 0 else "+$%d" % add)
        for h, add, lbl in HEIGHTS)
    return st, fo, co, hi


def form(compact=False):
    st, fo, co, hi = options_html()
    from content import UPGRADES
    ups = "".join(
        '<label class=chk><input type=checkbox name=upgrade value="%s" data-add="%d">'
        '<span><b>%s</b><em>%s</em></span><span class=amt>+$%d</span></label>'
        % (lbl, amt, lbl, note, amt) for lbl, amt, note in UPGRADES)
    return """
<form id=order class=panel novalidate>
  <h2 style="font-size:22px">Build your order</h2>
  <p class=hint style="margin:-2px 0 16px">No account, no checkout maze. You get a
  proof by email before anything is cut.</p>

  <div class=prev aria-live=polite>
    <div class=prevtxt id=prevtxt>TX 1234 AB</div>
    <div class=prevlbl id=prevlbl>3&quot; block characters &middot; one pair, pre-spaced</div>
  </div>

  <div class=total>
    <span class=n id=total>$19</span>
    <span class=lbl>your price</span>
    <span class=ship>Free shipping<br>Ships next business day</span>
  </div>

  <fieldset>
    <legend>What do you need?</legend>
    <div class=opts>
      <label class=opt><input type=radio name=kind value="Registration numbers" data-base="19" checked>
        <span>Registration numbers<em>$19 a pair</em></span></label>
      <label class=opt><input type=radio name=kind value="Boat name" data-base="29">
        <span>Boat name<em>from $29</em></span></label>
      <label class=opt><input type=radio name=kind value="Numbers + name" data-base="44">
        <span>Both<em>from $44, save $4</em></span></label>
      <label class=opt><input type=radio name=kind value="Something else" data-base="22">
        <span>Something else<em>decals, motor, carpet</em></span></label>
    </div>
  </fieldset>

  <div class=fieldrow>
    <div>
      <label for=f_text>Exactly what should it say?</label>
      <input type=text id=f_text name=text value="TX 1234 AB" autocomplete=off
             placeholder="TX 1234 AB" maxlength=40 required>
      <div class=hint id=texthint>Copy it straight off your registration card.</div>
    </div>
  </div>

  <div class="fieldrow two" style="margin-top:13px">
    <div>
      <label for=f_state>Your state</label>
      <select id=f_state name=state><option value="">Select&hellip;</option>""" + st + """
        <option value="Other">Other / not listed</option>
        <option value="USCG documented">USCG documented vessel</option></select>
    </div>
    <div>
      <label for=f_color>Colour</label>
      <select id=f_color name=color>""" + co + """</select>
    </div>
  </div>

  <fieldset style="margin-top:16px">
    <legend>Character height</legend>
    <div class=opts>""" + hi + """</div>
    <div class=hint>Federal rule is a 3&quot; minimum. Taller is always legal.</div>
  </fieldset>

  <div class=fieldrow>
    <div>
      <label for=f_font>Font</label>
      <select id=f_font name=font>""" + fo + """</select>
      <div class=hint id=fonthint>Registration numbers must be plain vertical block
      characters, so script fonts are locked out for numbers.</div>
    </div>
  </div>

  <fieldset style="margin-top:17px">
    <legend>Add anything?</legend>
    <div class=checks>""" + ups + """</div>
  </fieldset>

  <div class="fieldrow two">
    <div><label for=f_name>Your name</label>
      <input type=text id=f_name name=name autocomplete=name required></div>
    <div><label for=f_email>Email (your proof goes here)</label>
      <input type=email id=f_email name=email autocomplete=email required></div>
  </div>
  <div class="fieldrow two" style="margin-top:13px">
    <div><label for=f_phone>Phone (optional)</label>
      <input type=tel id=f_phone name=phone autocomplete=tel></div>
    <div><label for=f_boat>Boat make &amp; model (optional)</label>
      <input type=text id=f_boat name=boat placeholder="2004 Tracker Pro 170"></div>
  </div>
  <div class=fieldrow style="margin-top:13px">
    <div><label for=f_notes>Anything we should know?</label>
      <textarea id=f_notes name=notes rows=3 placeholder="Hull is dark blue - I want white. Rivets across the panel."></textarea></div>
  </div>

  <button type=submit class="btn lg" style="margin-top:18px" id=sub>
    Send my order &middot; <span id=btot>$19</span></button>
  <p class=hint style="margin-top:11px">We reply with a proof and a payment link.
  Nothing is cut and nothing is charged until you approve the proof.</p>
  <div id=msg role=status aria-live=polite style="margin-top:12px"></div>
</form>"""


JS = r"""
(function(){
  var f=document.getElementById('order'); if(!f) return;
  var SCRIPT=/script|vibes|edwardian|brush|lobster|old english|hobo/i;
  var tot=document.getElementById('total'), btot=document.getElementById('btot');
  var pv=document.getElementById('prevtxt'), pl=document.getElementById('prevlbl');
  var fontSel=document.getElementById('f_font'), fontHint=document.getElementById('fonthint');
  var textHint=document.getElementById('texthint'), txt=document.getElementById('f_text');
  var COL=window.BNS_COL||{};
  function kind(){var r=f.querySelector('[name=kind]:checked');return r?r:null;}
  function isNum(){var k=kind();return k && k.value.indexOf('Registration')===0;}

  function price(){
    var k=kind(), n=k?parseFloat(k.dataset.base):19;
    var h=f.querySelector('[name=height]:checked'); if(h) n+=parseFloat(h.dataset.add||0);
    var ups=f.querySelectorAll('[name=upgrade]:checked');
    for(var i=0;i<ups.length;i++){
      // "Add your boat name" is already in the base when they picked Both
      if(k && k.value==='Numbers + name' && /boat name/i.test(ups[i].value)) continue;
      n+=parseFloat(ups[i].dataset.add||0);
    }
    return Math.round(n);
  }
  function render(){
    var p='$'+price();
    tot.textContent=p; btot.textContent=p;
    var t=(txt.value||'').trim()||'YOUR BOAT';
    var h=f.querySelector('[name=height]:checked');
    var hv=h?h.value:'3';
    var fn=fontSel.value||'Block';
    var cl=document.getElementById('f_color');
    var cname=cl?cl.value:'White';
    pv.textContent=t;
    pv.style.fontFamily = SCRIPT.test(fn) ? 'Georgia,"Times New Roman",serif'
                                          : '"Arial Black",Impact,sans-serif';
    pv.style.fontStyle  = SCRIPT.test(fn) ? 'italic' : 'normal';
    pv.style.color      = COL[cname] || '#12242e';
    pv.style.textShadow = (cname.indexOf('White')===0||cname==='Chrome'||cname==='Reflective White')
                          ? '0 0 1px #6b7c86,0 1px 2px rgba(0,0,0,.35)' : 'none';
    var unit = isNum() ? 'one pair, pre-spaced' : 'one decal, pre-spaced';
    pl.textContent = hv+'" '+fn.replace(/ \(.*\)/,'')+' · '+cname+' · '+unit;

    // Registration numbers are legally required to be block characters.
    var lock=isNum();
    for(var i=0;i<fontSel.options.length;i++){
      var o=fontSel.options[i];
      o.disabled = lock && SCRIPT.test(o.value);
    }
    if(lock && SCRIPT.test(fontSel.value)) fontSel.selectedIndex=0;
    fontHint.textContent = lock
      ? 'Registration numbers must be plain vertical block characters, so script fonts are locked out.'
      : 'Any font works on a name or a decal. Script reads beautifully on a transom.';
    textHint.textContent = lock
      ? 'Copy it straight off your registration card, spaces and all.'
      : 'Capitalisation matters - we cut it exactly as typed.';
  }

  f.addEventListener('input',render);
  f.addEventListener('change',render);

  f.addEventListener('submit',function(ev){
    ev.preventDefault();
    var msg=document.getElementById('msg'), sub=document.getElementById('sub');
    var need=['f_text','f_name','f_email'];
    for(var i=0;i<need.length;i++){
      var el=document.getElementById(need[i]);
      if(!el.value.trim()){ el.focus();
        msg.innerHTML='<span class=bad>Fill in your '+
          (need[i]==='f_text'?'lettering':need[i]==='f_name'?'name':'email')+' first.</span>';
        return; }
    }
    var em=document.getElementById('f_email').value;
    if(!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(em)){
      msg.innerHTML='<span class=bad>That email does not look right.</span>';
      document.getElementById('f_email').focus(); return; }

    var d={}, fd=new FormData(f), ups=[];
    fd.forEach(function(v,k){ if(k==='upgrade'){ups.push(v);} else {d[k]=v;} });
    d.upgrades=ups.join(', ');
    d.quoted_total=price();
    d.page=location.pathname;

    sub.disabled=true; sub.textContent='Sending…';
    msg.textContent='';
    fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},
                        body:JSON.stringify(d)})
      .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
      .then(function(res){
        if(!res.ok) throw new Error(res.j && res.j.error || 'failed');
        f.innerHTML='<h2 style="font-size:23px">Got it — order '+
          (res.j.ref||'received')+'</h2>'+
          '<p>We are drawing your proof now. It lands in <strong>'+
          em.replace(/</g,'&lt;')+'</strong> shortly, with a payment link.</p>'+
          '<p class=hint>Nothing gets cut and nothing gets charged until you '+
          'reply <em>approved</em>. If the proof is wrong, say so and we redraw it free.</p>';
        f.scrollIntoView({block:'center'});
      })
      .catch(function(){
        sub.disabled=false; sub.textContent='Send my order';
        msg.innerHTML='<span class=bad>That did not go through. '+
          'Email <a href="mailto:orders@boatnumbershop.com">orders@boatnumbershop.com</a> '+
          'and we will pick it up by hand.</span>';
      });
  });
  render();
})();
"""

def color_js():
    pairs = ",".join('"%s":"%s"' % (n, h) for n, h in COLORS)
    return "window.BNS_COL={%s};" % pairs
