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
  "B.O.A.T.","Liquid Asset","Second Mortgage","Tax Write Off","Boat Payment","Debt Sentence",
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
      '<a class="btn lg" href="/design/">Put one of these on the transom &middot; from $38</a>';
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

# The DECODING is worker/decode.js - the same file the MCP server runs. This
# is only the page's rendering: read the box, call the shared decoder, draw the
# table. Before this, the decode logic lived here in a JS string and nowhere
# else, so putting it on the worker would have made a second copy of it.
HIN_JS = r"""
(function(){
  var D=window.NMB_DECODE; if(!D) return;
  var btn=document.getElementById('hinbtn'); if(!btn) return;
  var inp=document.getElementById('hin'), out=document.getElementById('hinout');
  function go(){
    var r=D.decodeHin(inp.value||'');
    out.classList.add('on');
    if(!r.ok){ out.innerHTML='<p class=bad>'+D.toHtml(r.msg)+'</p>'; return; }
    var rows=[['Manufacturer code (MIC)',
               r.mic+' &mdash; '+(r.manufacturer
                 ? '<strong>'+D.toHtml(r.manufacturer)+'</strong>'
                 : D.toHtml(r.manufacturer_note))],
              ['Hull serial number', r.serial]];
    if(r.built) rows.push(['Built', r.built]);
    if(r.model_year) rows.push(['Model year', r.model_year]);
    if(!r.built) rows.push(['Date code', r.date_code]);
    var notes=r.notes.map(function(n){
      return '<p class=hint style="margin-top:10px">'+D.toHtml(n)+'</p>';
    }).join('');
    out.innerHTML='<div class=tw><table><tbody>'+rows.map(function(x){
      return '<tr><th style="width:38%">'+x[0]+'</th><td>'+x[1]+'</td></tr>';
    }).join('')+'</tbody></table></div>'+notes+
    '<p style="margin-top:12px"><a href="/design/">We cut registration '+
    'numbers for $28 a pair.</a></p>';
  }
  btn.addEventListener('click',go);
  inp.addEventListener('keydown',function(ev){
    if(ev.key==='Enter'){ev.preventDefault();go();}});
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

    // prefix - the same table the order form uses
    var V = window.BNS_VALIDATE;
    if(V){
      var vr = V.check(raw);
      if(vr.level === 'vwarn' || vr.level === 'vnote'){
        add(false, vr.msg.replace(/<\/?strong>/g, ''));
      } else if(vr.state){
        add(true, 'Prefix reads as a <strong>'+vr.state+'</strong> number.');
      }
    }

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
      (pass?'<a class="btn lg" style="margin-top:6px" href="/design/">Order this set &middot; $28</a>':'');
    out.classList.add('on');
  }
  btn.addEventListener('click',go);
  inp.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();go();}});
  go();
})();
"""


# ---------------------------------------------------------- the funny page
#
# WHY THIS EXISTS. The page's title, meta description and share card all said
# "400 Funny Boat Names" while FUNNY_GROUPS above held 110 - one of which was
# listed twice, so 109 distinct. A listicle whose headline number is wrong in
# the <title> is the easiest thing on the site for a reader to disprove: they
# only have to scroll.
#
# The fix is not to lower the number. mcp/data/name_bank.json already holds
# nearly a thousand names that are tagged, levelled and sorted into lanes, and
# none of them were reaching this page. So the page now renders FROM the bank,
# and every printed count is DERIVED from what actually renders - there is no
# number typed anywhere for a build to drift away from.
#
# The six hand-curated groups above stay, and stay first. They are the
# editorial claim the page makes ("sorted by how the joke actually lands"),
# and a thousand names dumped alphabetically would be a worse page, not a
# bigger one.
import json as _json
import os as _os

# Lanes from the bank, in the order they appear on the page, with the heading
# a reader sees. `classy` is deliberately absent: those names are good, but
# they are not funny, and padding a funny list with them is the same lie in a
# different direction.
BANK_LANES = [
    ("double",      "Double meanings (read it twice)"),
    ("ironic",      "Ironic, if you know the boat"),
    ("deadpan",     "Deadpan, said with a straight face"),
    ("scratch",     "The ones that make people look twice"),
    ("wtf",         "Genuinely strange"),
    ("payments",    "What it cost you"),
    ("corporate",   "For the one who never really left the office"),
    ("retirement",  "Retired, and not quiet about it"),
    ("divorce",     "After the divorce"),
    ("couples",     "Bought together, named together"),
    ("fishing",     "Fishing, specifically"),
    ("pontoon",     "Pontoon energy"),
    ("food",        "Food and drink"),
    ("nerd",        "For the nerds"),
    ("genz",        "If your crew is under thirty"),
    ("midwest",     "Midwest, ope"),
    ("existential", "Existential, at 6am on flat water"),
    ("anagram",     "Anagrams and wordplay"),
    ("misspelled",  "Deliberately misspelled"),
]

_BANK = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                      "mcp", "data", "name_bank.json")


def funny_sections():
    """Every group on the funny page: (heading, [(name, dock_talk)]).

    Deduplicated across the WHOLE page, not per group - "Pour Decisions" was
    in two of the curated groups and so was counted twice by anything that
    trusted the group lengths.

    `dock_talk` is the bank's level_code 'd': fine on the boat, awkward read
    out over channel 16. The page marks those rather than dropping them,
    which is what the share card has always promised.
    """
    try:
        with open(_BANK, encoding="utf-8") as fh:
            bank = _json.load(fh)["names"]
    except (OSError, ValueError, KeyError):
        bank = []                       # the curated page still builds
    meta = {r["name"]: r for r in bank}

    def row(n):
        """(name, dock_talk, expansion).

        Metadata comes from the bank even for a curated name, because the bank
        is built FROM this file and the tagging pass is where the level and the
        note were recorded.

        The note is printed ONLY for a backronym. 254 names carry one, but most
        are glosses of the pun - "not working" under Knot Working - and this
        page's own copy says that a joke needing a setup is not a boat name.
        A backronym is the exception that proves it: B.O.A.T. is unreadable
        without "Break Out Another Thousand", because the expansion IS the
        name.
        """
        r = meta.get(n) or {}
        note = (r.get("tag_note") or r.get("note")
                if r.get("mechanism_code") == "ba" else None)
        return (n, r.get("level_code") == "d", note)

    out, seen = [], set()
    for g, names in FUNNY_GROUPS:
        rows = [row(n) for n in names if not (n in seen or seen.add(n))]
        if rows:
            out.append((g, rows))
    for lane, heading in BANK_LANES:
        rows = []
        for r in bank:
            n = r["name"]
            if (lane in (r.get("categories") or [])
                    and r.get("mechanism_code") != "sincere"
                    and n not in seen):
                seen.add(n)
                rows.append(row(n))
        if rows:
            out.append((heading, rows))
    return out


def funny_count():
    """How many names the page actually renders. Never typed, only counted."""
    return sum(len(rows) for _, rows in funny_sections())
