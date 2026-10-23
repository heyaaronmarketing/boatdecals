# -*- coding: utf-8 -*-
"""Tier-1 registration number validation.

Checks four things, in the order a typo is likely to occur:

  1. prefix is a real vessel prefix  (catches postal-code confusion: a
     Michigan owner typing MI, which is in fact Mississippi's prefix)
  2. shape is plausible              (prefix + up to 4 digits + up to 2 letters,
                                      with Maine's documented exception)
  3. groups are separated            (TX1234AB - we pre-space anyway, so this
                                      offers the corrected string)
  4. characters are issuable         (California never issues I, O or Q)

It WARNS. It never blocks.

The prefix table is compiled from secondary sources, states issue sequentially
so old hulls carry retired formats, and we only cover tier 1 of the rules. An
order refused by an incomplete validator is a lost sale; an order flagged for
the proof is a thirty-second check by someone who knows. The proof step exists
precisely so software does not have to be certain.
"""
from content import (VESSEL_PREFIX, PREFIX_STATE, FORMAT_EXCEPTIONS,
                     NO_LETTERS, POSTAL_MISTAKE)


def data_js():
    """Emit the tables the browser needs."""
    pref = ",".join('"%s":"%s"' % (p, s) for p, s in sorted(PREFIX_STATE.items()))
    noletters = ",".join('"%s":"%s"' % (k, v) for k, v in NO_LETTERS.items())
    mistake = ",".join('"%s":["%s","%s"]' % (p, st, v)
                       for p, (st, v) in sorted(POSTAL_MISTAKE.items()))
    return ("window.BNS_PREFIX_STATE={%s};window.BNS_NOLETTERS={%s};"
            "window.BNS_POSTAL_MISTAKE={%s};" % (pref, noletters, mistake))


JS = r"""
window.BNS_VALIDATE = (function(){
  var STATE = window.BNS_PREFIX_STATE || {};
  var NOLET = window.BNS_NOLETTERS || {};
  var OOPS  = window.BNS_POSTAL_MISTAKE || {};

  function clean(v){ return String(v||'').toUpperCase().replace(/[^A-Z0-9]/g,''); }

  /**
   * Returns {level, msg, fixed} - level is 'vok' | 'vnote' | 'vwarn'.
   * Prefixed because 'ok' and 'note' are already global CSS classes.
   * `fixed` is a correctly spaced version when we can derive one.
   * Nothing here ever prevents an order.
   */
  function check(raw){
    var compact = clean(raw);
    if(compact.length < 3) return {level:'vok'};

    var prefix = compact.slice(0,2);
    var rest = compact.slice(2);
    var state = STATE[prefix];

    // 1. prefix
    if(!state){
      // The common case by far: they typed the postal code. Say exactly what
      // they meant rather than making them go and look it up.
      var oops = OOPS[prefix];
      if(oops){
        var g = rest.match(/^(\d{1,4})([A-Z]{0,3})$/);
        var corrected = g
          ? oops[1]+' '+g[1]+(g[2] ? ' '+g[2] : '')
          : oops[1]+' '+rest;
        return {level:'vwarn', fixed: corrected,
          msg:'<strong>'+oops[0]+'</strong> boat numbers start with '
              +'<strong>'+oops[1]+'</strong>, not '+prefix+' &mdash; the vessel '
              +'prefixes were set before the postal codes. Check your card.'};
      }
      return {level:'vwarn',
        msg:'<strong>'+prefix+'</strong> is not a vessel prefix we recognise. '
            +'Check it against your registration card &mdash; a few states '
            +'differ from the postal code.'};
    }

    // 2. shape
    var m = rest.match(/^(\d{1,4})([A-Z]{0,3})$/);
    if(!m){
      return {level:'vwarn',
        msg:'That does not read as <strong>'+prefix+' &lt;numbers&gt; '
            +'&lt;letters&gt;</strong>. Copy it off the card exactly &mdash; '
            +'we cut what you type.'};
    }
    var digits = m[1], letters = m[2];

    var shapeOk;
    if(prefix === 'ME'){
      shapeOk = /^\d{2}[A-Z]{3}$/.test(rest) || /^\d{4}[A-Z]$/.test(rest);
      if(!shapeOk){
        return {level:'vnote',
          msg:'Maine numbers usually run <strong>ME 12ABC</strong> or '
              +'<strong>ME 1234A</strong>. We will cut it as typed &mdash; '
              +'just worth a second look.'};
      }
    } else if(letters.length > 2){
      return {level:'vnote',
        msg:'Most states end in one or two letters. We will cut it as typed, '
            +'but check the card.'};
    }

    // 3. characters a state will not issue
    var banned = NOLET[prefix];
    if(banned){
      for(var i=0;i<banned.length;i++){
        if(letters.indexOf(banned[i]) > -1){
          return {level:'vnote',
            msg:state+' does not issue the letters <strong>'+banned.split('').join(', ')
                +'</strong> in a number. Worth checking that is not a '
                +'0 or a 1.'};
        }
      }
    }

    // 4. spacing - offer the corrected string rather than scolding
    var fixed = prefix + ' ' + digits + (letters ? ' ' + letters : '');
    var typedGroups = String(raw||'').trim().split(/[\s-]+/).filter(Boolean).length;
    if(typedGroups < 2){
      return {level:'vnote', fixed: fixed,
        msg:'The rule wants a gap between the groups. We will cut it as '
            +'<strong>'+fixed+'</strong>.'};
    }

    return {level:'vok', state:state, fixed:fixed};
  }

  return {check: check, clean: clean};
})();
"""
