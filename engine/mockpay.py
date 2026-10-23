# -*- coding: utf-8 -*-
"""Sandbox card form - looks and behaves like Stripe's Payment Element, talks
to nobody.

Why this exists: the shop needs a working end-to-end demo (and a way to test the
order pipeline) before Stripe keys are issued.

The TEST MODE banner was removed from the field at the owner's request, so the
only remaining on-screen signal is on the confirmation. The guard against a
sandbox build reaching the production domain now lives in build.py - see
assert_pay_mode_is_safe().

The hard rule this file enforces: **a full card number never leaves the browser
and is never stored.** The field accepts any digits so testing is frictionless,
but on submit only the detected brand and the last four are put in the payload.
The PAN and CVC are read, formatted, validated for shape, and discarded. The
worker additionally refuses any field that still looks like a full card number,
so a future edit here cannot quietly start leaking one.

"""

HTML = """
<div class=sfield>
  <label for=cc_num>Card number</label>
  <div class=sinput id=cc_numwrap>
    <input type=text id=cc_num inputmode=numeric autocomplete="off"
           placeholder="1234 1234 1234 1234" maxlength=23 aria-describedby=cc_err>
    <span class=brands id=cc_brand>
      <i data-b=visa>VISA</i><i data-b=mc>MC</i><i data-b=amex>AMEX</i><i data-b=disc>DISC</i>
    </span>
  </div>
</div>
<div class=srow>
  <div class=sfield>
    <label for=cc_exp>Expiry</label>
    <div class=sinput><input type=text id=cc_exp inputmode=numeric
      placeholder="MM / YY" maxlength=7 autocomplete="off"></div>
  </div>
  <div class=sfield>
    <label for=cc_cvc>CVC</label>
    <div class=sinput><input type=text id=cc_cvc inputmode=numeric
      placeholder="CVC" maxlength=4 autocomplete="off"></div>
  </div>
  <div class=sfield>
    <label for=cc_zip>ZIP</label>
    <div class=sinput><input type=text id=cc_zip inputmode=numeric
      placeholder="50707" maxlength=10 autocomplete="off"></div>
  </div>
</div>
<div class=scerr id=cc_err role=alert></div>

"""

CSS = """
.sfield{margin-bottom:8px;flex:1 1 0;min-width:0}
.sfield label{display:block;font-size:12px;font-weight:600;color:#30313d;margin-bottom:4px}
.srow{display:flex;gap:7px}
.sinput{position:relative;display:flex;align-items:center;background:#fff;
border:1px solid #e6e6e9;border-radius:8px;
box-shadow:0 1px 1px rgba(0,0,0,.03),0 3px 6px rgba(0,0,0,.02);
transition:border-color .12s,box-shadow .12s}
.sinput:focus-within{border-color:#1d7a48;box-shadow:0 0 0 3px rgba(29,122,72,.18)}
.sinput.bad{border-color:#df1b41}
.sinput.bad:focus-within{box-shadow:0 0 0 3px rgba(223,27,65,.16)}
.sinput input{width:100%;border:0;background:none;font:inherit;font-size:16px;
padding:9px 11px;color:#30313d;min-height:40px;letter-spacing:.01em}
.sinput input:focus{outline:0}
.sinput input::placeholder{color:#a3a3ad}
.brands{display:flex;gap:4px;padding-right:9px;flex:0 0 auto}
.brands i{font-style:normal;font-size:9.5px;font-weight:800;letter-spacing:.02em;
color:#8b8b96;background:#f2f2f5;border:1px solid #e3e3e8;border-radius:3px;
padding:3px 4px;line-height:1;opacity:.5;transition:opacity .12s,background .12s}
.brands.on i{opacity:.18}
.brands.on i.lit{opacity:1;background:#1a1f36;color:#fff;border-color:#1a1f36}
.scerr{color:#df1b41;font-size:12.4px;font-weight:600;min-height:1px;margin-top:-3px}

.paying .sinput{opacity:.6;pointer-events:none}
"""

JS = r"""
window.BNS_MOCKPAY = (function(){
  var $=function(i){return document.getElementById(i);};

  function digits(s){ return String(s||'').replace(/\D/g,''); }

  function brandOf(n){
    if(/^4/.test(n)) return ['visa','Visa'];
    if(/^(5[1-5]|2[2-7])/.test(n)) return ['mc','Mastercard'];
    if(/^3[47]/.test(n)) return ['amex','Amex'];
    if(/^6(011|5|4[4-9])/.test(n)) return ['disc','Discover'];
    return ['',''];
  }
  function isAmex(n){ return /^3[47]/.test(n); }

  function groupPan(n, amex){
    if(amex) return n.replace(/^(\d{1,4})(\d{1,6})?(\d{1,5})?.*$/,
      function(_,a,b,c){ return [a,b,c].filter(Boolean).join(' '); });
    return (n.match(/.{1,4}/g)||[]).join(' ');
  }

  function wire(){
    var num=$('cc_num'), exp=$('cc_exp'), cvc=$('cc_cvc'), zip=$('cc_zip'),
        brands=$('cc_brand'), err=$('cc_err');
    if(!num) return;

    num.addEventListener('input',function(){
      var d=digits(num.value), amex=isAmex(d);
      d=d.slice(0, amex?15:19);
      num.value=groupPan(d, amex);
      cvc.maxLength = amex?4:3;
      var b=brandOf(d)[0];
      brands.classList.toggle('on', d.length>0);
      [].forEach.call(brands.children,function(i){
        i.classList.toggle('lit', !!b && i.dataset.b===b); });
      clear();
    });

    exp.addEventListener('input',function(){
      var d=digits(exp.value);
      // "2" can only be February, and "22" is not a month - in both cases the
      // first digit is a single-digit month and wants a leading zero. Stripe
      // does the same, so "229" becomes 02 / 29 rather than 22 / 9.
      if(d.length>=1 && +d.charAt(0)>1) d='0'+d;
      else if(d.length>=2 && +d.slice(0,2)>12) d='0'+d;
      d=d.slice(0,4);
      exp.value = d.length>2 ? d.slice(0,2)+' / '+d.slice(2) : d;
      clear();
    });
    exp.addEventListener('keydown',function(ev){
      if(ev.key==='Backspace' && /\s\/\s$/.test(exp.value))
        exp.value=exp.value.replace(/\d\s\/\s$/,'');
    });

    cvc.addEventListener('input',function(){
      cvc.value=digits(cvc.value).slice(0, isAmex(digits(num.value))?4:3); clear(); });
    zip.addEventListener('input',function(){
      zip.value=zip.value.replace(/[^0-9A-Za-z \-]/g,'').slice(0,10); clear(); });

    function clear(){
      err.textContent='';
      ['cc_numwrap'].concat([]).forEach(function(){});
      [].forEach.call(document.querySelectorAll('.sinput.bad'),function(e){
        e.classList.remove('bad'); });
    }
  }

  function fail(el,msg){
    var err=$('cc_err');
    err.textContent=msg;
    if(el){ el.closest('.sinput').classList.add('bad'); el.focus(); }
    return null;
  }

  /**
   * Validates SHAPE only - deliberately not a Luhn check, because the whole
   * point is that any test number works. Returns {brand, last4} and nothing
   * else: the PAN and CVC stay in this function and are never returned,
   * logged, or sent anywhere.
   */
  function collect(){
    var num=$('cc_num'), exp=$('cc_exp'), cvc=$('cc_cvc');
    var d=digits(num.value), amex=isAmex(d);
    if(d.length < (amex?15:13)) return fail(num,'Your card number is incomplete.');
    var e=digits(exp.value);
    if(e.length<4) return fail(exp,'Your card’s expiry date is incomplete.');
    var mm=+e.slice(0,2), yy=+e.slice(2,4);
    if(mm<1||mm>12) return fail(exp,'Your card’s expiry month is invalid.');
    var now=new Date(), curY=now.getFullYear()%100, curM=now.getMonth()+1;
    if(yy<curY || (yy===curY && mm<curM))
      return fail(exp,'Your card’s expiry date is in the past.');
    if(digits(cvc.value).length < (amex?4:3))
      return fail(cvc,'Your card’s security code is incomplete.');
    return {brand: brandOf(d)[1] || 'Card', last4: d.slice(-4)};
    // d, cvc and zip go out of scope here. Nothing above this line is returned.
  }

  return {wire: wire, collect: collect,
          fail: function(m){ return fail(null, m); }};
})();
"""
