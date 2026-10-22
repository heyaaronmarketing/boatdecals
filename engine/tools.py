# -*- coding: utf-8 -*-
"""The three interactive tools. These are the traffic assets: the name cluster
(~10,900/mo, LOW competition) and the HIN/hull-number cluster (~4,500/mo, LOW)
are both bigger and softer than the commercial terms, and they feed the
money pages."""

# ---------------------------------------------------------- boat names
NAME_SETS = {
 "Classic": ["Serenity","Andiamo","Second Wind","Island Time","Destiny","Freedom",
   "Liberty","Perseverance","Odyssey","Tranquility","Escape","Legacy","Aurora",
   "Solstice","Kismet","Equinox","Meridian","Nauti Girl","Sea Breeze","True North",
   "Blue Horizon","Calypso","Dauntless","Endeavour","Fair Winds","Grace","Halcyon",
   "Intrepid","Journey","Harmony","Morning Star","Northern Light","Pelican",
   "Quicksilver","Resolute","Sanctuary","Tempest","Vigilant","Wanderer","Zephyr"],
 "Funny": ["Knot Working","Buoy Oh Buoy","Aquaholic","Ship Faced","Nauti Buoy",
   "Seas the Day","Piers Pressure","Multiple Scoregasms","Codfather","The Codfather",
   "Reel Lucky","Hooked Up","Baitin Around","Fishful Thinking","Vitamin Sea",
   "Sail La Vie","Knot on Call","Knot Guilty","Wet Dream","Pier Pressure",
   "Usually Sober","Shore Thing","Breaking Wind","Bad Mussel","Boat Vibes Only",
   "Gone Fission","Keel Over","Sofishticated","Current Sea","Nacho Boat",
   "Knot Paid For","Debt Sentence","Marina Del Broke","Seaduction","Wave Goodbye",
   "Just Add Water","Pour Decisions","Liquid Assets","Gone Coastal","Ships Happen"],
 "Retirement": ["Our Turn","Finally","Last Resort","No Alarm Clock","Retired & Wired",
   "Done Working","Pension Plan","Severance","Grandkids Inheritance","Spent It",
   "Worth the Wait","Thirty Years","Clocked Out","Early Out","The Reward",
   "No More Mondays","Permanent Vacation","Golden Hours","Time Served","Sunset Clause"],
 "Money": ["Liquid Asset","Sea Note","Boat Payment","Second Mortgage","Tax Write Off",
   "Deductible","Interest Only","Overdraft","Dry Powder","Bull Market","Dividend",
   "Capital Gain","Net Worth","Compound Interest","Margin Call","Loose Change",
   "Sunk Cost","Depreciating","Escrow","Pretax"],
 "Fishing": ["Reel Deal","Set the Hook","Drag On","Live Bait","Fish Tales","Big Rig",
   "Knot Tired","Last Cast","Dawn Patrol","Tight Lines","Chum Bucket","Gaffer",
   "Trolling Along","Off the Hook","Bent Rod","Screaming Drag","Bite Me","Dead Sticking",
   "Blue Water","Sonar","Deep Drop","Full Stringer","Limit Out","Hook Line Sinker"],
 "Nautical": ["Starboard","Leeward","Windward","Dead Reckoning","Rhumb Line","Astern",
   "Beam Reach","Close Haul","Spinnaker","Bowline","Keelhaul","Deadrise","Gunwale",
   "Transom","Bilge Rat","Mizzen","Jibe Ho","Luffing","Hard to Port","Weather Helm"],
}
ADJ = ["Salty","Lucky","Lazy","Wild","Silver","Midnight","Southern","Restless",
       "Crimson","Hidden","Rogue","Quiet","Golden","Reckless","Barefoot","Rusty",
       "Second","Lone","Stubborn","Happy","Shallow","Deep","Sunday","Borrowed"]
NOUN = ["Mistress","Lady","Pearl","Dollar","Anchor","Compass","Current","Tide",
        "Reef","Wake","Harbour","Lagoon","Mariner","Drifter","Nomad","Rascal",
        "Dolphin","Osprey","Marlin","Mallard","Minnow","Gypsy","Siren","Vagabond"]

FUNNY_GROUPS = [
 ("Puns that actually land", [
  "Knot Working","Buoy Oh Buoy","Seas the Day","Sail La Vie","Pier Pressure",
  "Sofishticated","Current Sea","Codfather","Gone Fission","Fishful Thinking",
  "Aquaholic","Vitamin Sea","Nauti Buoy","Keel Over","Shore Thing","Wave Goodbye",
  "Reel Lucky","Hooked Up","Multiple Scoregasms","Baitin Around","Knot Guilty",
  "Pour Decisions","Gone Coastal","Ships Happen","Just Add Water","Seaduction"]),
 ("The money jokes", [
  "Liquid Asset","Second Mortgage","Tax Write Off","Boat Payment","Debt Sentence",
  "Knot Paid For","Marina Del Broke","Sunk Cost","Depreciating Asset","Interest Only",
  "Margin Call","Overdraft","Spent It","Pretax","Net Worth","Loose Change",
  "The Deductible","Escrow","Dry Powder","Severance"]),
 ("Retirement bragging", [
  "Our Turn","Finally","No Alarm Clock","Done Working","Pension Plan","Clocked Out",
  "No More Mondays","Thirty Years","Permanent Vacation","Time Served","Early Out",
  "Grandkids Inheritance","The Reward","Worth the Wait","Golden Hours","Last Resort"]),
 ("Honest about the drinking", [
  "Usually Sober","Ship Faced","Wet Dream","Pour Decisions","Breaking Wind",
  "Boat Vibes Only","Nacho Boat","Bad Mussel","Liquid Lunch","Rum Runner",
  "Dark & Stormy","Painkiller","Happy Hour","Last Call","One More Round"]),
 ("Fishing, specifically", [
  "Reel Deal","Set the Hook","Last Cast","Tight Lines","Chum Bucket","Screaming Drag",
  "Bent Rod","Off the Hook","Limit Out","Full Stringer","Dawn Patrol","Live Bait",
  "Bite Me","Hook Line Sinker","Trolling Along","Deep Drop","Dead Sticking","Drag On"]),
 ("Marriage commentary (order at your own risk)", [
  "Her Boat","She Said Yes","The Other Woman","Permission Granted","Second Wife",
  "Mistress","Alimony","Wife Approved","Happy Wife","Yes Dear","Veto Power",
  "Joint Account","My Turn Next","Negotiated","The Compromise"]),
]

NAME_JS = r"""
(function(){
  var S=window.BNS_NAMES||{}, A=window.BNS_ADJ||[], N=window.BNS_NOUN||[];
  var out=document.getElementById('nameout'); if(!out) return;
  function pick(a){return a[Math.floor(Math.random()*a.length)];}
  function spin(){
    var k=document.getElementById('namestyle').value;
    var list = k==='Mix' ? [] : (S[k]||[]);
    var res=[], used={};
    for(var i=0;i<12;i++){
      var v;
      if(k==='Mix'||!list.length||Math.random()<0.28){ v=pick(A)+' '+pick(N); }
      else { v=pick(list); }
      if(used[v]){ i--; continue; } used[v]=1; res.push(v);
    }
    out.innerHTML='<div class=names>'+res.map(function(n){
      return '<div>'+n.replace(/</g,'&lt;')+'</div>';}).join('')+'</div>'+
      '<a class="btn lg" href="/design/">Put one of these on the transom &middot; from $29</a>';
    out.classList.add('on');
  }
  document.getElementById('spin').addEventListener('click',spin);
  document.getElementById('namestyle').addEventListener('change',spin);
  spin();
})();
"""

# ------------------------------------------------------------- HIN decoder
# MIC codes are assigned by the US Coast Guard. This is a partial table of the
# manufacturers that actually show up on used boats - enough to answer most
# lookups, with an honest "not in our table" fallback.
MIC = {
 "BUJ":"Bayliner","BIY":"Bayliner","SERT":"Sea Ray","SER":"Sea Ray","XTT":"Sea Ray",
 "BWC":"Boston Whaler","BWCE":"Boston Whaler","GDY":"Godfrey / Hurricane",
 "TRK":"Tracker Marine","BUH":"Tracker / Nitro","LDN":"Lund","LUN":"Lund",
 "GTH":"Grumman","ALU":"Alumacraft","AWT":"Alumacraft","CRS":"Crestliner",
 "PRC":"Princecraft","STR":"Starcraft","SMC":"Smoker Craft","RGF":"Ranger Boats",
 "RGR":"Ranger Boats","SKE":"Skeeter","SKI":"MasterCraft","MBC":"MasterCraft",
 "MLB":"Malibu Boats","CCB":"Correct Craft / Nautique","NAU":"Nautique",
 "CBT":"Chaparral","CHP":"Chaparral","GWA":"Grady-White","GDW":"Grady-White",
 "PYC":"Pursuit","RBH":"Robalo","WEL":"Wellcraft","WLC":"Wellcraft",
 "FGC":"Four Winns","FWN":"Four Winns","GLA":"Glastron","LRB":"Larson",
 "CRU":"Crownline","CRX":"Crownline","MON":"Monterey","REG":"Regal",
 "COB":"Cobalt","CTC":"Cobia","KEY":"Key West","CAR":"Carolina Skiff",
 "CSK":"Carolina Skiff","SEA":"Sea Hunt","SHT":"Sea Hunt","SCT":"Scout",
 "PAT":"Pathfinder","MAK":"Mako","MKO":"Mako","HYD":"Hydra-Sports",
 "TIA":"Tiara","CAT":"Catalina Yachts","CTY":"Catalina Yachts","HUN":"Hunter Marine",
 "HMX":"Hunter Marine","BEN":"Beneteau","JBO":"J Boats","PEA":"Pearson",
 "ODY":"O'Day","CAL":"Cal Yachts","ERY":"Ericson","ISL":"Islander",
 "YAM":"Yamaha","YMA":"Yamaha WaveRunner","BRP":"Sea-Doo / BRP","ZZN":"Sea-Doo",
 "KAW":"Kawasaki","PLT":"Polaris","CAJ":"Cajun","PRO":"ProCraft","STS":"Stratos",
 "TID":"Tidewater","SEF":"Sea Fox","NAX":"NauticStar","BLZ":"Blazer",
 "XPR":"Xpress Boats","GTR":"G3 Boats","WRB":"War Eagle","LOW":"Lowe Boats",
 "LWB":"Lowe Boats","SUN":"Sun Tracker","BEN2":"Bennington","BNN":"Bennington",
 "HAR":"Harris","SYL":"Sylvan","PBC":"Premier Pontoons","MAN":"Manitou",
 "AVL":"Avalon","QWE":"Qwest","PLY":"Playbuoy","WLD":"Weldcraft",
}

HIN_JS = r"""
(function(){
  var MIC=window.BNS_MIC||{};
  var btn=document.getElementById('hinbtn'); if(!btn) return;
  var inp=document.getElementById('hin'), out=document.getElementById('hinout');
  var MO={A:'January',B:'February',C:'March',D:'April',E:'May',F:'June',
          G:'July',H:'August',I:'September',J:'October',K:'November',L:'December'};
  function esc(s){return String(s).replace(/</g,'&lt;');}
  function go(){
    var v=(inp.value||'').toUpperCase().replace(/[\s-]/g,'');
    out.classList.add('on');
    if(v.length<12){
      out.innerHTML='<p class=bad>A hull identification number is exactly 12 '+
        'characters. You entered '+v.length+'. Check the starboard side of the '+
        'transom, up near the top edge.</p>'; return;
    }
    if(v.length>12){
      out.innerHTML='<p class=bad>That is '+v.length+' characters. A HIN is exactly 12 - '+
        'no more. Drop any trailing text.</p>'; return;
    }
    if(!/^[A-Z]{3}/.test(v)){
      out.innerHTML='<p class=bad>The first three characters should be letters '+
        '(the manufacturer code). Yours are &ldquo;'+esc(v.slice(0,3))+'&rdquo;.</p>'; return;
    }
    var mic=v.slice(0,3), serial=v.slice(3,8), d=v.slice(8,12);
    var maker=MIC[mic];
    var rows=[];
    rows.push(['Manufacturer code (MIC)', mic + (maker ? ' &mdash; <strong>'+maker+'</strong>'
      : ' &mdash; not in our table. It is a valid-looking code; search the USCG MIC database for the builder.')]);
    rows.push(['Hull serial number', serial]);

    // Post-1984 format: positions 9-10 = month letter + year digit, 11-12 = model year.
    var out2='';
    var m1=d.charAt(0), y1=d.charAt(1), my=d.slice(2);
    if(MO[m1] && /^\d$/.test(y1) && /^\d{2}$/.test(my)){
      var modelYear = (parseInt(my,10) > 40 ? '19' : '20') + my;
      rows.push(['Built', MO[m1]+' '+( (parseInt(my,10)>40?'19':'20') +
        my.charAt(0) + y1 )]);
      rows.push(['Model year', modelYear]);
      out2='<p class=hint style="margin-top:10px">Read as the current (post-August 1984) '+
        'format: characters 9&ndash;10 are the build month and year, 11&ndash;12 are the model year.</p>';
    } else if(/^\d{2}/.test(d)) {
      rows.push(['Date code', d + ' &mdash; this looks like the pre-1984 format, '+
        'where the last characters are the model year and month.']);
    } else {
      rows.push(['Date code', d + ' &mdash; we could not read this as a standard date block. '+
        'Straight-year formats were common before August 1984.']);
    }
    out.innerHTML='<div class=tw><table><tbody>'+rows.map(function(r){
      return '<tr><th style="width:38%">'+r[0]+'</th><td>'+r[1]+'</td></tr>';
    }).join('')+'</tbody></table></div>'+out2+
    '<p style="margin-top:12px"><strong>A HIN is not your registration number.</strong> '+
    'The HIN is stamped into the hull by the builder and never changes. Your registration '+
    'number is issued by your state and is the one you have to display in 3-inch letters. '+
    '<a href="/design/">We cut those for $19 a pair.</a></p>';
  }
  btn.addEventListener('click',go);
  inp.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();go();}});
})();
"""

# --------------------------------------------------------- layout checker
LAYOUT_JS = r"""
(function(){
  var btn=document.getElementById('chkbtn'); if(!btn) return;
  var inp=document.getElementById('chknum'), hsel=document.getElementById('chkh'),
      hull=document.getElementById('chkhull'), col=document.getElementById('chkcol'),
      out=document.getElementById('chkout');
  var DARK={'White':0,'Yellow':0,'Light Blue':0,'Silver':0,'Chrome':0,'Tan':0,
            'Black':1,'Navy':1,'Red':1,'Forest':1,'Burgundy':1,'Grey':1};
  function go(){
    var raw=(inp.value||'').toUpperCase().trim();
    var h=parseFloat(hsel.value), rows=[], pass=true;
    function add(ok,txt){ rows.push('<tr><td>'+(ok?'<span class=ok>PASS</span>':
      '<span class=bad>FIX</span>')+'</td><td>'+txt+'</td></tr>'); if(!ok) pass=false; }

    // height
    add(h>=3, h>=3 ? h+'&quot; characters clear the 3&quot; federal minimum.'
      : h+'&quot; is under the 3&quot; federal minimum. Go up to 3&quot; or taller.');

    // block characters
    add(true,'Block characters: we cut registration numbers in plain vertical block '+
      'only, so this is handled for you.');

    // contrast
    var hv=hull.value, cv=col.value;
    var hd=DARK[hv], cd=DARK[cv];
    var ok = !(hd===undefined||cd===undefined) ? (hd!==cd) : true;
    add(ok, ok ? cv+' on a '+hv.toLowerCase()+' hull contrasts clearly.'
      : cv+' on a '+hv.toLowerCase()+' hull will not contrast. '+
        'Federal rule requires the characters to contrast with the background &mdash; '+
        'switch to '+(hd? 'White or Yellow':'Black or Navy')+'.');

    // format + spacing
    var groups=raw.split(/[\s-]+/).filter(function(x){return x;});
    var compact=raw.replace(/[\s-]/g,'');
    var shaped=/^[A-Z]{2}[\s-]*\d+[\s-]*[A-Z]{0,2}$/.test(raw);
    add(groups.length>=2, groups.length>=2
      ? 'Spacing is right &mdash; '+groups.length+' groups separated, '+
        'which is what the rule asks for.'
      : 'No spaces or hyphens found. The rule wants a space or hyphen the width of a '+
        'letter between the letter and number groups, like <strong>TX 1234 AB</strong>.');
    add(shaped||groups.length>=2, shaped
      ? 'Reads as a standard state format: letters, numbers, letters.'
      : 'Double-check this against your registration card &mdash; it does not match the '+
        'usual prefix-digits-suffix shape.');
    add(compact.length>=4 && compact.length<=8, (compact.length>=4&&compact.length<=8)
      ? compact.length+' characters is a normal length.'
      : compact.length+' characters is unusual. Most state numbers are 6 to 8.');

    // physical width estimate: block chars average ~0.62 of cap height, plus spacing
    var w = Math.round((compact.length*h*0.62 + (groups.length-1)*h*0.55)*10)/10;
    out.innerHTML='<div class="big" style="margin-bottom:10px">'+
      (pass?'<span class=ok>Looks legal.</span>':'<span class=bad>Needs a fix.</span>')+
      '</div><div class=tw><table><thead><tr><th style="width:84px">Check</th>'+
      '<th>What we found</th></tr></thead><tbody>'+rows.join('')+'</tbody></table></div>'+
      '<p style="margin-top:12px">Your set will finish roughly <strong>'+w+
      '&quot; wide</strong> per side at '+h+'&quot; tall. Measure the forward half of your '+
      'hull before you order &mdash; you need that much flat run above the waterline.</p>'+
      (pass?'<a class="btn lg" style="margin-top:6px" href="/design/">Order this set &middot; $19</a>':'');
    out.classList.add('on');
  }
  btn.addEventListener('click',go);
  inp.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();go();}});
  go();
})();
"""
