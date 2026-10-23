# -*- coding: utf-8 -*-
"""The boat name generator.

Ported from Aaron's standalone prototype. The name bank, the category list and
the personalised templates are his, verbatim - that content is the whole point
of the tool and it is not something to paraphrase.

What changed in the port, and why:

* The prototype shipped its own page chrome and its own palette (cream, navy,
  orange). Here it renders inside the site shell and uses the site tokens, so
  there is one design system rather than two.
* The transom preview offers the TEN FONTS WE ACTUALLY CUT, built from
  content.FONTS, instead of four faces picked for the mockup. Three of the
  four were already loaded for the order wizard; the rest cost nothing extra
  and the preview now shows faces you can really order.
* "Cut this name" deep-links /design/?name=...&port=..., and the wizard was
  taught to read those. Before this it dropped the name on the floor.
* The hailing-port add-on price came out - add-ons are not sold on the site.
"""
from content import FONTS

NAMES_JS = r"""
(function(){
var N = {
double: ["Knot On Call","Reel Estate","Shore Thing","Pier Pressure","Current Affairs","Fishful Thinking","Buoy Oh Buoy","Dock Holiday","Sea Señor","Moor Problems","Knot Guilty","Hull Of A Time","Stern Warning","Berth Control","Aft Thoughts","Keel Me Softly","Sea Section","Liquid Assets","Fluid Situation","Sail Tax","Moor Than Enough","Knot Today","Wake Me Up","Tide Together","Mast Confusion","Prop Culture","Helm Yeah","Rudder Than You","Trim Reaper","Seas & Desist","Jib Jab","Anchor Management","Ex Marks The Spot","Main Squeeze","Knot Worth It","Oar-dinary","Row-mance","Hull Lotta Love","Line Dancing","Berth Day Present","Aqua-holic","Sternly Worded","Dead Reckoning","Drag Queen","Pi Rates","Cast Away My Troubles","Bow Movement","Knot A Problem","Moor Or Less","Hull Yeah","Keel Over Laughing","Tide & True","Port Decision","Wake Up Call","Fender Bender","Sea Nile","Sea Esta","Water Bored","Marlin Monroe","Bass Ackwards","Sole Mates","Oh Buoy","Bilge Pump Up The Jam","Nauti Buoy","Reel Smooth","Piece Of Ship","Shipfaced","Nautical But Nice","Knot So Fast","In Deep Ship"],
deadpan: ["I Named It After Nothing","Water, But Organized","An Island Is A Boat That Stopped","I Own This Part Of The Lake Until I Leave","Technically I'm Ahead Of The Fish","A Motor Is Rowing With Opinions","The Lake Was Here First","This Boat Has Never Been Lost. I Have.","Anchored, Emotionally","Fishing: Sitting With Hope","A Dock Is A Boat That Gave Up","An Anchor Is A Rock With A Job","I Was Gonna Swim","Not A Boat, A Very Slow Plane","Technically A Bathtub","Ducks Think I'm One Of Them","The Lake Is Soup With No Flavor","Fishing Is Waiting With Equipment","A Wave Is Water In A Hurry","Bought This Instead Of Therapy","I Have A Boat. I Don't Have A Plan.","Kayaks Are Boats That Won't Let You Stand","I Can Also Not Swim On Land","A Sail Is A Flag With Ambition","Floats Fine, Steers Eventually","I Asked For A Sandwich","Used To Be A Tree","My Life Raft Has A Boat","It's Mostly Water Out Here","Pontoons Are Training Wheels","I Named It Later","The Fish Have A Boat Too, It's Bigger","Water Is Just Wet","I Don't Own It, I Rent The Lake","Fish Don't Know It's Thursday","Boat Is A Verb Now","The Horizon Keeps Moving","I'm Not Lost, The Lake Is","Rowing Is Walking For Your Arms","It Floats On Purpose","A Boat Is A Hole You Pour Money In","Half Of Fishing Is Lying","I Brought Snacks, Not A Plan","Some Days You're The Lure","This Is Where I Think","Marinas Are Parking Lots That Float","I'm Mostly Sunscreen Now","The Lake Doesn't Know My Name","Still Not A Pirate","It's Only A Yacht If I Say So","My Boat Has A Boat","Every Dock Is A Bridge That Quit","Fish Are Just Wet Birds","I Peaked In This Boat"],
ironic: ["Fast","Quiet","Well Maintained","Reliable","Trusted Brand","Factory Fresh","Pristine","Smooth Ride","Brand Loyal","Economy Class","Legal Limit","Sober Captain","No Regrets","Perfect Condition","Dry Dock","Land Lover","Hates Water","Desert Storm","Sinks","Unsinkable (Terms Apply)","Brand New Used Boat","Flood Insurance","Pending Sale","Cash Buyer","Paid Off","Fully Insured","On Time","Low Maintenance","Fuel Efficient","Empty Tank","Totally Legal","Mostly Sober","Dock Queen","Never Leaves The Slip","Trailer Queen","Working Overtime","Business Trip","Tax Deductible","Good Decision","Budget Friendly","Silent Partner","Swim Lesson","Sinking Feeling","Perfectly Calm","Rowboat Energy","Slow Leak","Still Floats","Professionally Named","Quiet Cruise","Gas Station","Speed Limit","Bigger Than It Looks","Adult Supervision","Early Retirement","Designated Driver","Emergency Fund","The Responsible One","Weekday Boat","Great Resale Value","Family Friendly","Final Answer","Under Warranty","Wife Approved","Needs Nothing"],
wtf: ["Lasagna","Uncle Rick's Fault","Mildly Damp","Aggressively Beige","Fish Lawyer","The Loud One","Goose Negotiator","Yes This Is Dog","Deck Lizard","Marinara","Twelve Raccoons","Lake Dad Energy","Hot Potato","Floating Nap Hazard","Sock Full Of Lake","Grandpa's Ashes","Possum Wagon","Wet Couch","Cheese Barge","Sponsored By Nobody","Human Floatie","Mayonnaise","Not A Cult","Chad's Mistake","Two Hot Dogs","Church Bus","Lawnmower","Kevin","Big Soup","Aggressively Average","Beige","It's Fine","Honk If Lonely","Yes, It's Loud","Haunted","Sentient","Moist","Moisture Enthusiast","Trust Me","Goose Patrol","Nacho Boat","Suspicious Package","Snack Barge","Ask Me About My Grandkids","I Am Not The Captain","Mid","Lake Goblin","The Tetanus","Pontoon Of Doom","Hot Tub Time Boat","Emotional Support Boat","Wet Hot Midwestern Summer","Loud Fish","Larry","Free Candy","Sweaty","Dairy Queen Of The Lake","Birthday Clown","Ham","Regret Barge","Not Haunted (Lie)","Cousin Eddie","Gas Station Sushi","Bees?","Legally A Boat","Dad's Boat (Mom's Idea)","Beaver Fever","Wet Bandit","Sorry Not Sorry","Oops All Lake","Grandma Energy","The Bad Decision","Lake Flavored","Just Float, Carl"],
scratch: ["Not The Boat You're Looking For","Page Intentionally Left Blank","See Attached","Name Redacted","Version 3 (Final) FINAL","Rough Draft","Under Review","TBD","Last Year's Name","Unsubscribe","Reply STOP To Cancel","Terms Apply","May Contain Boat","Error: Name Too Long","Loading Name...","Boat","Unnamed","Your Ad Here","Not For Sale (Make Offer)","Starboard Is Left*","This Side Up","Was Here First","Who's Driving?","Decoy","Plot Twist","Loading…","404 Boat Not Found","The Sequel","Previously Owned","Déjà Vu (Again)","Allegedly","To Be Continued","Does This Float","Ask Your Wife","Citation Needed","Insert Name Here","Default Name","Password123","Untitled (1)","New Document","Rhymes With Orange","The Boat Formerly Known As","I Don't Know Her","Other Boat","Not Pictured","Whose Boat?","Same Boat","Wrong Boat","Decaf","Objects In Mirror","Rounding Error","Schrödinger's Boat","Minimum Wake","Control Group","Placeholder","See Other Side","Name Pending Approval","Read The Manual","Pending","Exhibit A","Hypothetically","Results May Vary","Not To Scale","Draft 1","Third Boat","Blink Twice If Stuck","Hold My Spot","Nobody's Boat","No Comment","Fine Print","Thought Experiment","Ask Again Later","Still Loading","You Are Here","Optional"],
anagram: [
 {n:"Canoe Ocean",note:"Canoe and Ocean are anagrams of each other"},
 {n:"Cat Pain",note:"anagram of Captain"},
 {n:"Epic Rap",note:"anagram of Crappie"},
 {n:"Yell Awe",note:"anagram of Walleye"},
 {n:"No Top On",note:"anagram of Pontoon"},
 {n:"Rancho",note:"anagram of Anchor"},
 {n:"Airman",note:"anagram of Marina"},
 {n:"Aloft",note:"anagram of Float"},
 {n:"Tutor",note:"anagram of Trout"},
 {n:"Leek",note:"anagram of Keel"},
 {n:"Rents",note:"anagram of Stern"},
 {n:"Diet Tide",note:"Diet and Tide are anagrams"},
 {n:"Lake Leak",note:"Lake and Leak are anagrams"},
 {n:"Lake Kale",note:"Lake and Kale are anagrams"},
 {n:"Reel Leer",note:"Reel and Leer are anagrams"},
 {n:"Rule Lure",note:"Rule and Lure are anagrams"},
 {n:"Weak Wake",note:"Weak and Wake are anagrams"},
 {n:"Horse Shore",note:"Horse and Shore are anagrams"},
 {n:"Hoser",note:"anagram of Shore"},
 {n:"Ripe Pier",note:"Ripe and Pier are anagrams"},
 {n:"Master Stream",note:"Master and Stream are anagrams"},
 {n:"Reskin",note:"anagram of Sinker"},
 {n:"Amber Bream",note:"Amber and Bream are anagrams"},
 {n:"Actual In",note:"anagram of Nautical"},
 {n:"Tag Tear",note:"anagram of Regatta"},
 {n:"Curies",note:"anagram of Cruise"},
 {n:"Growin'",note:"anagram of Rowing"},
 {n:"Unsets",note:"anagram of Sunset"},
 {n:"Pots Stop",note:"Pots and Stop are anagrams"},
 {n:"Mats Mast",note:"Mats and Mast are anagrams"},
 {n:"Ails Sail",note:"Ails and Sail are anagrams"},
 {n:"Cash Fit",note:"anagram of Catfish"},
 {n:"Crap",note:"anagram of Carp. We stand by it."},
 {n:"Soar Oars",note:"Soar and Oars are anagrams"},
 {n:"Hoya",note:"anagram of Ahoy"},
 {n:"Terns",note:"anagram of Stern"},
 {n:"Edit Tide",note:"Edit and Tide are anagrams"},
 {n:"Tamers",note:"anagram of Stream"}
],
pontoon: ["Pontoon Legend","Floating Patio","Dad's Lazy River","Wake Zone? Never Heard Of Her","The Slow Lane","Deck Boss","Dock Rocket (0-5 MPH)","Grandpa's Toon","Toon Town","Sunset Specialist","Party Barge Rules","Floating Deck","Slow Roll","Dad Speed","Coozie Cruiser","Sunscreen Mandatory","Shirt Optional, Dad Bod Required","Pontoon Platoon","No Wake Zone Legend","The Back Porch","Living Room II","Cup Holder Count: 14","Bluetooth Boat","Nap Deck","5 MPH Lifestyle","Floating Garage","Lake Mayor","HOA Of The Water","Tuesday Boat","Grill Sergeant","Toon Squad","Porch With A Motor","Slow Is Smooth","Koozie Krew","Deck Chair Admiral","Snack Captain","Cooler Full, Tank Empty","Floating Recliner","The Lazy Susan","Cruise Control","Low Speed Legend","The Dadmiral","Sun's Out, Toons Out","Pontoon Saloon","Chill Factor","Mild Wake","Beer:30","Flip Flop Fleet","Bass Boat Envy","The Toon Lagoon"],
payments: ["Payment 12 Of 240","Floating Debt","0% APR","Repo Bait","Kids' Inheritance","College Fund","401(k)oozie","Bankrupt-Sea","Interest Only","Second Mortgage","Tax Refund","Overdraft","Buy High, Sell Low","Depreciating","Line Of Credit","Monthly Nut","The Bonus","Rent Is Due","Financed Fun","Overtime Pays","Still Owe On It","Boat Payment","Credit Score","Collateral","Minimum Payment","Liquidated","Bad With Money","The Raise","Sold The Truck","Pre-Approved","Reverse Mortgage","Bank's Boat","Co-Signed","Paid In Full*","Late Fee","Cheaper Than Divorce","Expensive Nap","Ask My Accountant","Debt Sea","Hull Of A Loan"],
divorce: ["Her Half","Settlement","Split Decision","Alimony Alley","Exhibit B","She Got The House","Court Ordered Fun","Dissolved","Irreconcilable Deck","Second Act","Custody Weekend","Half The Boat","Freedom 45","Final Decree","My Lawyer's Boat","Lake Therapy","The Prenup","Single Again","Divorcé Deck","Keep The Ring","Separate Checks","Clean Break","Rebound","Ex-Wife's Nightmare","Ex-Husband's Dream","Won In Court","Joint Custody","New Chapter","Sole Survivor","Moving On","Unmarried Vessel","No Longer Attached","Her Reason","Amicable","Spite Boat","Petition Granted","Fresh Start","The Bachelor","Independence Day","Mediation"],
existential: ["Just Passing Through","Where Does The Lake End","We Were Never Lost","Only Water","Ask The Horizon","Same Lake, Different Day","Time Is A Flat Lake","Was That It","Nobody Asked","Ripples","Why Are We Here","Nothing Matters, Float","Aging Gracefully","Running Out Of Time","Temporary","Impermanence","We Are All Just Drifting","Inevitable","The Void (But Wet)","Borrowed Time","Mortality Barge","Still Here","One Day","Later","Eventually","Memento Moor-i","Is This It","Fine, Thanks","Existential Crisis II","Slightly Content","Meaning Pending","Here For Now","Drifting With Intent","The Long Exhale","Nobody's Watching","Dust & Water","Okay I Guess","The Middle Part","Unfinished","Quiet Desperation","Not Yet","A Brief Moment","This Too Shall Float","Both Lost & Found","Peace, Allegedly","Just Floating Through","Out Of Reach","Enough","Still Learning","No Destination"],
misspelled: ["Bote","Yott","Da Bote","Kanoe","Yaht","Seriusly","Fast Bote Go Zoom","Unsinkabel","Luxery","Nautikal","Titanik","Thee Boat","Sea Ya Layter","Big Bote","Lil Bote","Phloat","Buoyant Bois","Reel Gud","Boat Goes Fast","Lake Lyfe","Ahoyy","Speling Bee","Kaptin","Anchorz Away","Fysh","Marinah","Shure Thing","Gon Fishn","Nawt Guilty","Boatiful"],
midwest: ["Ope!","Oh Fer Cute","Pop Not Soda","Walleye Weekend","Hotdish","Corn Fed","Ope, Scuse Me","Just Gonna Sneak Past Ya","Lutefisk","Iowa Nice","Hawkeye Honey","Cheese Curd Cruiser","Dairy Air","Wind Chill","Tornado Watch","Puddle Jumper","Ice Out","Bratwurst Barge","Casserole","Ranch On Everything","Supper Club","Up Nort","Lake Day, Don'tcha Know","Duck Duck Grey Duck","Bag Of Ice","Gravel Road","Bean Walker","Detasseler","Cedar Valley Vibes","Lake Life, Iowa Style","Knee High By July","Corn Hole","Field Of Dreamboats","Sconnie","Cheese Head","Hot Beef Sandwich","Side Of Ranch","Bring A Jacket","Lake Effect","Midwest Goodbye"],
corporate: ["Synergy","Circle Back","Let's Take This Offline","Per My Last Email","Out Of Office","Low-Hanging Fruit","Q4 Goals","Bandwidth","Move The Needle","Touch Base","Parking Lot","Deep Dive","KPI","Stakeholder","Disruptor","Pivot","Agile","Scalable","Deliverables","Hard Stop At 5","Unlimited PTO","Reply All","Zoom Fatigue","Quiet Quitter","Exit Interview","Severance","Golden Parachute","Work-Lake Balance","Thought Leader","Team Building","Offsite","Core Competency","Best Practice","Bleeding Edge","Mission Critical","ROI","Boil The Ocean","Run It Up The Flagpole","Open Door Policy","Ping Me"],
nerd: ["Buoyancy","Displacement","Archimedes","Eureka (Spilled)","Newton's Third Boat","Hydrodynamic Mess","Surface Tension","Bernoulli's Barge","Terminal Velocity (Slow)","Error 404","Ctrl+Alt+Float","Unsinkable.exe","Beta Version","Boat 2.0","Patch Notes","Quantum Leak","Low Resolution","Uncertainty Principle","Sine Wave","H2 Oh No","Carbon Dated","Lab Rat","Hull Integrity 74%","Respawn","Lag","Extra Life","Side Quest","Press X To Float","Admin","Null","Prototype","Open Source","Legacy System","Version Control","Ship It","Floating Point","Hypothesis","Peer Reviewed","Water Table","Big Bang Barge"],
horror: ["Final Destination","The Deep End","Don't Turn Around","Catfish Noodle Of Doom","It Follows (Slowly)","Weeds Have Hands","Sunken Hopes","The Dock At Midnight","Night Of The Living Bass","Eerie Canal","The Undertow","Lake Monster","Final Girl","Night Swim","Don't Look Down","Something Touched My Foot","Dead Ahead","Davy's Locker","Creature Feature","Haunted By Payments","It Came From The Bilge","Fog Bank","Dead Calm","The Thing In The Weeds","Ghost Of Dad's Last Boat","Bermuda Try-Angle","Shallow Grave","The Drop Off","Nope","What Was That","Undertoad","Slightly Haunted","Cursed But Floats","Lake Of The Damp","Open Water","Last Seen Wednesday","Don't Go In The Water (I Did)","The Sunken Place","Creepy Crawlies","Gone Fishin' Forever","Jump Scare","The Sequel Nobody Wanted","Fin","Below Deck","Midnight Launch","Carp Diem Of The Dead","Scream Queen","Rest In Reeds","The Swamp Thing","Silent Hull"],
fishing: ["Reel Therapy","Bass-ic Instinct","Crappie Day","Fish Whisperer","Walleye Wrangler","Catch Up","Hooked","Fishin' Impossible","The Catfish Lie","Bait & Switch","Lures & Lies","Minnow Bucket","Bass Pro Shopper","No Fish Were Harmed","The Big Lie","Tell Me About The One","Livewell","Trolling","Off The Hook","Fish On!","Crappie Hour","Catch & Release Program","Walleye Wednesday","Sunfish Daddy","Lure Of The Lake","Jig's Up","Outfished Again","Skunked","Limit Reached","Reel Men Fish","Hook Line & Stinker","Bobber Fett","Carp Diem","Bite Me","Fish Tales","Pole Position","Reel Deal","Crappie Attitude","Bass To The Future","Walleye Can't Quit You"],
retirement: ["Pension Plan","Spent It","Grandkids' Toy","Social Security","65 & Floating","Nap Time","Medicare Part Sea","Early Bird","The Golden Years","No Alarm Clock","Retired & Rehired","Lake Time","Senior Discount","Reel Retired","Every Day Is Saturday","Worked 40 Years For This","Out To Pasture","Grandpa's Office","Finally","Bucket List","Zero Meetings","Gold Watch","Last Paycheck","Clocked Out","Pension Pending","Still Got It","Grandma's Getaway","Done Working","Time Served","The Long Weekend","Semi-Retired, Fully Floating","Sunset Clause","Second Childhood","Weekday Warrior","Twilight Zone","Forever Friday","Office Closed","Legacy","Second Wind","Hall Pass"],
couples: ["Her Idea","His Idea, Her Name","Marriage Counselor","Date Night","Anniversary Gift (To Me)","Happy Wife Happy Lake","Compromise","She Said Yes (To The Boat)","Separate Vacations","The Guest Room","Our Other Mortgage","Honeymoon Phase","Mom's Night Off","Dad's Dog House","Couples Therapy","Argument Settler","Nap Together","Still Married","Negotiated","Peace Offering","She Picked The Color","We'll Discuss It Later","Mutual Decision*","Ask Her","Hers On Weekends","The Apology","Yes Dear","Sleeping Arrangements","Second Honeymoon","In This Together","Love & Bilge Water","Long Story","Team Effort","Marital Bliss (Floating)","Two Captains","Both Wrong","Date Night Debt","Patient Wife","Ring Replacement","Till Dock Do Us Part"],
food: ["Fish Fry Friday","Gravy Boat","Soup","Walleye Taco","Snack Attack","Buoy-rrito","Reel Cheesy","Brats & Boats","Nacho Average Boat","Lake Trout Tuesdays","Ice Cream Social","Wet Burrito","Deviled Egg","Potato Salad","Casserole Cruise","Bologna Barge","Floating Picnic","Tacos On The Water","Cheese Plate","Cookie Dough","Hot Sauce","Extra Pickles","Pizza Rolls","Beer Cheese","Cold Cuts","Buttered Corn","Jello Salad","Pork Chop","Salt & Vinegar","Sweet Tea","Beef Jerky","Dad's Secret Rub","Sloppy Joe","Crock Pot","Float Beer","Snack Size","Second Breakfast","Nachos Overboard","Walleye Wednesday Special","Corn Dog"],
genz: ["No Cap","It's Giving Boat","Main Character","Slay The Lake","Lowkey Floating","Vibe Check","Touch Grass? No, Water","Rizz Boat","Delulu","Boat Era","Big Yikes","Sus","Not Me Buying A Boat","POV: Lake","Soft Launch","Hard Launch","Situationship","Understood The Assignment","Core Memory","Serving Looks & Fish","Caught In 4K","Bussin'","Living Rent Free","Cringe","Periodt","Unbothered","Mood","Iconic","Basic","Send It","Flex","Lake Girlie","Lake Boy Summer","Chronically Online","Outside Era","Plot Armor","Low Battery","The Ick","Snack Era","Left On Read"],
classy: ["Low Tide","Bluestem","Calm Season","Cold Spring","Slate & Pine","Quiet Fire","Wren","Long Light","The Quiet Hour","Honeylocust","Northern Light","Quiet Water","Last Light","Morning Glass","Still Point","Alder & Oak","Still Harbor","True North","Evensong","Harbor Lights","Meridian","Clearwater","Luna Grey","Driftwood","Blue Hour","Halcyon","Windward","Amber Wake","Fair Lead","Lodestar","Slack Water","Long Reach","Kestrel","Vesper","Kingfisher","First Light","Gloaming","Cedar Hollow","Nightjar","Lantern","Ember","Solace","Juniper","Tallgrass","Quietude","Wild Rice","North Star","Old Oak","Heron","Prairie Sky"]};

var MINE = ["{N}'s Nauti Buoy","Reel {N}","{N} Or Nothing","Knot {N}'s Problem","{N} Overboard","Captain {N} Was Here","{N}'s Last Nerve","The {N} Family Tax Write-Off","Sir {N} Of The Lake","{N}'s Retirement Plan","{N}'s Other Half","Property Of {N}","{N} Made Me Do It","{N} Was Right","Sorry, {N}","{N}'s Midlife Crisis","{N} Pays For Gas","Ask {N}","Don't Tell {N}","Hold My Beer, {N}","{N} Found Nemo","{N}: Not Responsible","Moby {N}","{N}tanic","{N}'s Bad Idea","{N} Is Driving","Blame {N}","{N} Time","{N}'s Office","Sea {N} Later","{N} & Sons (Allegedly)","{N}'s Boat, {N}'s Rules","Vitamin {N}","{N}'s Second Marriage","The {N} Situation","Nautical {N}","Mama {N}'s Getaway","{N} Has Left The Dock","Knot Without {N}","{N} Vs. The Lake","{N}'s Wet Dream Came True","{N} Said No","Big {N} Energy","{N}'s Side Hustle"];

var CATS = [
 ["surprise","🎲 Surprise me","Every category in the bucket"],
 ["double","🪝 Double meanings","Puns with a second layer"],
 ["deadpan","🎤 Deadpan one-liners","Mitch Hedberg energy"],
 ["ironic","🙃 Ironic","Says the opposite of what it is"],
 ["wtf","🤨 WTF","Names that stop traffic"],
 ["scratch","🧠 Head scratchers","Makes the dock do a double take"],
 ["anagram","🔀 Anagrams","Real rearrangements of real boat words"],
 ["pontoon","🍺 Pontoon dad","5 mph lifestyle"],
 ["payments","💸 Boat payments","Financed fun"],
 ["divorce","⚖️ Divorce settlement","Court-ordered freedom"],
 ["couples","💍 Married life","Compromise, floating"],
 ["existential","🌫️ Existential","Why are we here (the lake)"],
 ["horror","👻 Slightly haunted","Something touched my foot"],
 ["misspelled","🔤 Spelled wrong on purpose","Bote"],
 ["midwest","🌽 Midwest nice","Ope"],
 ["corporate","📊 Corporate buzzwords","Circle back on the water"],
 ["nerd","🧪 Nerd","Physics, bugs, respawns"],
 ["fishing","🎣 Fishing lies","Tell me about the one"],
 ["retirement","⛱️ Retirement","Every day is Saturday"],
 ["food","🌮 Snacks","Floating picnic"],
 ["genz","📱 Gen Z","It's giving boat"],
 ["classy","🕯️ Actually classy","For the person who hated all of the above"],
 ["mine","✨ Riff on my name","Type a name above"]];
"""


# The ten faces we cut, offered as transom previews. Block first - it is what
# most names end up in - and the script faces last.
def font_buttons():
    out = []
    for i, (lbl, css, _spec, _block) in enumerate(FONTS):
        out.append('<button type=button data-css="%s"%s>%s</button>'
                   % (css.replace('"', "&quot;"), " class=on" if i == 0 else "", lbl))
    return "".join(out)


def markup():
    return """
<div class="panel ngpanel">
  <div class=ngrow>
    <div class=nglab>1 &middot; Pick a vibe</div>
    <div class=nghint>Press <kbd>space</kbd> to spin &middot; <kbd>S</kbd> for
      surprise me</div>
  </div>
  <div class=ngcats id=ngcats></div>

  <div class=nglab style="margin-bottom:8px">2 &middot; Optional: riff on a name</div>
  <div class=ngfields>
    <div class=ngfield>
      <label for=ngwho>Your name, or the boat&rsquo;s old one</label>
      <input id=ngwho type=text maxlength=24 autocomplete=off
             placeholder="Dave, Gretchen, Mulligan">
    </div>
    <div class=ngfield>
      <label for=ngport>Hailing port</label>
      <input id=ngport type=text maxlength=28 autocomplete=off
             placeholder="Evansdale, IA">
    </div>
  </div>
  <div class=nghint style="margin-top:8px">Type a name and the
    <b>Riff on my name</b> category lights up with 40-odd personalised jabs.
    The hailing port is a preview flourish &mdash; it shows under the name here so you can see the whole transom, and is not carried into the order. We cut hailing ports; just ask when you order.</div>

  <div class=ngctl>
    <button type=button class="btn ngspin" id=ngspin>Spin 12 names</button>
    <button type=button class="btn ghost" id=ngmore>Keep these, add 12 more</button>
    <span class=nghint id=ngcount></span>
  </div>
</div>

<div class=nggrid id=nggrid></div>

<div class=ngtray id=ngtray hidden>
  <div class=ngtraybox>
    <b>Saved</b>
    <div class=nglist id=ngsaved></div>
    <button type=button class="btn sm ghost" id=ngcopyall>Copy list</button>
    <button type=button class="btn sm ghost" id=ngclearall>Clear</button>
  </div>
</div>

<div class=ngmodal id=ngmodal role=dialog aria-modal=true aria-labelledby=ngmname>
  <div class=ngsheet>
    <button type=button class=ngx id=ngclose aria-label="Close">&times;</button>
    <h2 id=ngmname style="margin:0 0 3px;font-size:22px"></h2>
    <div class=nghint id=ngmnote style="margin:0 0 12px"></div>

    <div class=ngcolors>Vinyl:
      <button type=button data-c="#ffffff" style="background:#fff" aria-label="White"></button>
      <button type=button data-c="#111111" style="background:#111" aria-label="Black"></button>
      <button type=button data-c="#c0c0c0" aria-label="Silver"
              style="background:linear-gradient(135deg,#eee,#9a9a9a)"></button>
      <button type=button data-c="#5fc4f5" style="background:#5fc4f5" aria-label="Blue"></button>
      <button type=button data-c="#b4541a" style="background:#b4541a" aria-label="Red"></button>
    </div>

    <div class=ngtransom id=ngtransom>
      <div><div class=ngtxt id=ngttxt></div><div class=ngport id=ngtport></div></div>
    </div>
    <div class=ngfonts id=ngfonts>__FONTS__</div>

    <div class=ngradio id=ngmradio></div>
    <div class=ngtests id=ngmtests></div>

    <div class=ngfoot>
      <div class=ngacts>
        <button type=button class="btn sm ghost" id=ngmsave>Save</button>
        <button type=button class="btn sm ghost" id=ngmcopy>Copy</button>
        <button type=button class="btn sm ghost" id=ngmshare>Share</button>
      </div>
      <a class="btn ngcut" id=ngmcut href="/design/">Cut this name &middot; from $29</a>
    </div>
  </div>
</div>
<div class=ngtoast id=ngtoast role=status aria-live=polite></div>
""".replace("__FONTS__", font_buttons())


CSS = """
/* ---------- name generator ---------- */
.ngpanel{padding:18px}
.ngrow{display:flex;gap:12px;flex-wrap:wrap;align-items:center;
justify-content:space-between}
.nglab{font-weight:800;font-size:15px;color:var(--ink)}
.nghint{font-size:13px;color:var(--mut);margin:0}
.nghint b{color:var(--ink)}
kbd{font:inherit;font-size:12px;border:1px solid var(--line);border-bottom-width:2px;
border-radius:5px;padding:0 5px;background:#fff}

.ngcats{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 16px}
.ngcat{border:1px solid var(--line);background:#fff;border-radius:999px;
padding:8px 13px;font:inherit;font-size:14px;font-weight:650;cursor:pointer;
color:var(--ink);white-space:nowrap;transition:border-color .15s,transform .15s}
.ngcat:hover{border-color:var(--nav2);transform:translateY(-1px)}
.ngcat.on{background:var(--nav);color:#fff;border-color:var(--nav)}
.ngcat.special{border-style:dashed}
.ngcat.armed{border-style:solid;background:var(--selbg)}
.ngcat.armed.on{background:var(--nav);color:#fff}

.ngfields{display:grid;gap:10px;grid-template-columns:1fr}
@media(min-width:640px){.ngfields{grid-template-columns:1.4fr 1fr}}
.ngfield label{display:block;font-size:12px;font-weight:700;color:var(--mut);
margin-bottom:4px}
.ngfield input{width:100%;font:inherit;font-size:15px;padding:10px 12px;
border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink)}
.ngfield input:focus{outline:2px solid var(--nav2);outline-offset:1px;
border-color:var(--nav2)}

.ngctl{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:16px}
.btn.ngspin{font-size:16px}
.btn.ghost{background:#fff;color:var(--nav);border:1.5px solid var(--line)}
.btn.ghost:hover{background:var(--soft);border-color:var(--nav2)}
.btn.sm{padding:8px 13px;font-size:13.5px;min-height:0}

.nggrid{display:grid;gap:12px;margin-top:18px;
grid-template-columns:repeat(auto-fill,minmax(248px,1fr))}
.ngcard{background:#fff;border:1px solid var(--line);border-radius:12px;
padding:14px 14px 10px;display:flex;flex-direction:column;gap:8px;cursor:pointer;
transition:border-color .15s,box-shadow .15s,transform .15s;animation:ngpop .3s both}
.ngcard:hover{border-color:var(--nav2);transform:translateY(-2px);
box-shadow:0 10px 24px -14px rgba(14,58,82,.5)}
@keyframes ngpop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.ngcard{animation:none}}
.ngtag{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
color:var(--mut)}
.ngname{font-size:26px;line-height:1.08;font-weight:800;color:var(--nav);
letter-spacing:-.01em;word-break:break-word}
.ngnote{font-size:12.5px;color:var(--mut);font-style:italic;margin-top:-4px}
.ngmeta{display:flex;gap:6px;flex-wrap:wrap;margin-top:auto}
.ngchip{font-size:11px;font-weight:700;padding:3px 8px;border-radius:999px;
background:var(--selbg);color:var(--ink)}
.ngchip.ok{background:#dcf0e6;color:var(--ok)}
.ngchip.warn{background:#fae6da;color:var(--warn)}
.ngacts2{display:flex;gap:4px;justify-content:flex-end;align-items:center;
border-top:1px dashed var(--line);padding-top:8px}
.ngic{appearance:none;border:0;background:transparent;cursor:pointer;font:inherit;
font-size:15px;padding:4px 8px;border-radius:7px;color:var(--mut);line-height:1}
.ngic:hover{background:var(--soft);color:var(--nav)}
.ngic.saved{color:var(--warn)}
.ngic.cut{font-size:12px;font-weight:800;color:#fff;background:var(--nav);
padding:6px 11px}
.ngic.cut:hover{background:var(--nav2);color:#fff}
.ngempty{grid-column:1/-1;text-align:center;color:var(--mut);padding:30px 10px}

.ngtray{position:sticky;bottom:0;z-index:5;margin-top:18px}
.ngtraybox{display:flex;gap:10px;align-items:center;flex-wrap:wrap;
background:var(--nav);color:#fff;border-radius:12px;padding:12px 14px}
.nglist{display:flex;gap:6px;flex-wrap:wrap;flex:1}
.ngsv{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);
border-radius:999px;padding:4px 10px;font-size:13px;display:inline-flex;gap:6px;
align-items:center}
.ngsv button{all:unset;cursor:pointer;opacity:.7;font-size:15px;line-height:1}
.ngsv button:hover{opacity:1}
.ngtraybox .btn.ghost{background:transparent;color:#fff;border-color:rgba(255,255,255,.4)}
.ngtraybox .btn.ghost:hover{background:rgba(255,255,255,.12);border-color:#fff}

.ngmodal{position:fixed;inset:0;background:rgba(6,28,42,.72);display:none;
align-items:center;justify-content:center;padding:16px;z-index:60}
.ngmodal.open{display:flex}
.ngsheet{position:relative;background:var(--soft);border-radius:16px;max-width:760px;
width:100%;max-height:92vh;overflow:auto;padding:20px}
.ngx{position:absolute;top:8px;right:12px;font-size:26px;line-height:1;
background:none;border:0;cursor:pointer;color:var(--mut);padding:4px 8px}
.ngx:hover{color:var(--ink)}
.ngcolors{display:flex;gap:7px;align-items:center;margin-bottom:9px;font-size:13px;
color:var(--mut)}
.ngcolors button{width:25px;height:25px;border-radius:50%;border:2px solid #fff;
box-shadow:0 0 0 1px var(--line);cursor:pointer;padding:0}
.ngcolors button:focus-visible{outline:2px solid var(--nav2);outline-offset:2px}
.ngtransom{background:linear-gradient(180deg,#1d5a7a,#0e3a52 55%,#082435);
border-radius:18px 18px 60px 60px/18px 18px 40px 40px;min-height:190px;display:flex;
align-items:center;justify-content:center;padding:32px 24px 42px;position:relative;
overflow:hidden;box-shadow:inset 0 -18px 40px rgba(0,0,0,.35),
inset 0 2px 0 rgba(255,255,255,.15)}
.ngtransom:before{content:"";position:absolute;left:0;right:0;bottom:0;height:34px;
background:linear-gradient(180deg,rgba(255,255,255,0),rgba(170,220,255,.22));
border-radius:0 0 60px 60px/0 0 40px 40px}
.ngtxt{color:#fff;text-align:center;font-size:clamp(26px,7vw,60px);line-height:1.05;
word-break:break-word;text-shadow:0 2px 0 rgba(0,0,0,.25)}
.ngport{color:rgba(255,255,255,.85);font-size:clamp(11px,2.2vw,16px);text-align:center;
margin-top:10px;letter-spacing:.14em;text-transform:uppercase;font-weight:700}
.ngfonts{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}
.ngfonts button{border:1px solid var(--line);background:#fff;border-radius:8px;
padding:7px 11px;cursor:pointer;font:inherit;font-size:13.5px;color:var(--ink)}
.ngfonts button.on{background:var(--nav);color:#fff;border-color:var(--nav)}
.ngradio{background:var(--nav);color:#bdf0d3;border-radius:10px;padding:12px 14px;
font-size:14px;margin:8px 0 12px;line-height:1.5}
.ngtests{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
margin:12px 0}
.ngtest{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:10px 12px;font-size:13px}
.ngtest b{display:block;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;
color:var(--mut);margin-bottom:3px}
.ngfoot{display:flex;gap:10px;flex-wrap:wrap;align-items:center;
justify-content:space-between;margin-top:10px}
.ngacts{display:flex;gap:6px;flex-wrap:wrap}
.btn.ngcut{font-size:15px}
.ngtoast{position:fixed;bottom:86px;left:50%;transform:translateX(-50%) translateY(16px);
background:var(--ink);color:#fff;padding:10px 17px;border-radius:999px;font-size:14px;
opacity:0;transition:.22s;pointer-events:none;z-index:70}
.ngtoast.show{opacity:1;transform:translateX(-50%) translateY(0)}
"""


NAMES_JS += r"""
var $=function(s){return document.querySelector(s);};
var grid=$('#nggrid'), catsEl=$('#ngcats'), who=$('#ngwho'), port=$('#ngport');
if(!grid) return;
var cat='surprise', shown=[], saved=[], cur=null;
try{ saved=JSON.parse(localStorage.getItem('bns_saved')||'[]'); }catch(e){ saved=[]; }
if(!Array.isArray(saved)) saved=[];

function norm(x){ return typeof x==='string' ? {n:x} : {n:x.n, note:x.note}; }
function pool(c){
  if(c==='mine'){
    var w=who.value.trim(); if(!w) return [];
    var W=w.replace(/\b\w/g,function(m){return m.toUpperCase();});
    return MINE.map(function(t){ return {n:t.replace(/\{N\}/g,W), cat:'mine'}; });
  }
  if(c==='surprise'){
    var all=[];
    Object.keys(N).forEach(function(k){
      N[k].forEach(function(x){ var o=norm(x); o.cat=k; all.push(o); });
    });
    if(who.value.trim()) all=all.concat(pool('mine'));
    return all;
  }
  if(!N[c]) return [];
  return N[c].map(function(x){ var o=norm(x); o.cat=c; return o; });
}
function label(k){
  var c=CATS.filter(function(x){return x[0]===k;})[0];
  return c ? c[1].replace(/^\S+\s/,'') : k;
}
function pick(k, avoid){
  var p=pool(cat).filter(function(x){ return avoid.indexOf(x.n)<0; });
  for(var i=p.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=p[i]; p[i]=p[j]; p[j]=t; }
  return p.slice(0,k);
}

/* The three tests the page promises, run on every card. */
function letters(n){ return n.replace(/[^A-Za-z0-9]/g,'').length; }
function width(n){
  return Math.round(n.replace(/\s/g,'').length*2.5 + (n.split(/\s+/).length-1)*1.5);
}
function radio(n){
  var L=letters(n), w=n.trim().split(/\s+/).length, p=/[^A-Za-z0-9\s']/.test(n);
  if(L<=12 && w<=3 && !p) return ['ok','Radio: easy'];
  if(L<=18 && w<=4) return ['','Radio: workable'];
  return ['warn','Radio: mouthful'];
}
function fitw(n){
  var w=width(n);
  return w<=30?['ok','~'+w+'" wide']:w<=48?['','~'+w+'" wide']:['warn','~'+w+'" · big transom'];
}
function esc(s){
  return String(s).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
  });
}
function cutUrl(n){ return '/design/?name='+encodeURIComponent(n); }

function card(x){
  var r=radio(x.n), f=fitw(x.n), isS=saved.indexOf(x.n)>-1;
  var el=document.createElement('div');
  el.className='ngcard'; el.dataset.n=x.n; el.tabIndex=0;
  el.innerHTML='<div class=ngtag>'+esc(label(x.cat))+'</div>'
   +'<div class=ngname>'+esc(x.n)+'</div>'
   +(x.note?'<div class=ngnote>'+esc(x.note)+'</div>':'')
   +'<div class=ngmeta><span class="ngchip '+r[0]+'">'+r[1]+'</span>'
   +'<span class="ngchip '+f[0]+'">'+f[1]+'</span></div>'
   +'<div class=ngacts2>'
   +'<button type=button class="ngic sv'+(isS?' saved':'')+'" aria-label="Save">'
   +(isS?'♥':'♡')+'</button>'
   +'<button type=button class="ngic cp" aria-label="Copy">⧉</button>'
   +'<button type=button class="ngic cut">Cut it →</button></div>';
  el.addEventListener('click',function(ev){
    var t=ev.target;
    if(t.classList.contains('sv')){ toggleSave(x.n); return; }
    if(t.classList.contains('cp')){ copy(x.n); return; }
    if(t.classList.contains('cut')){ location.href=cutUrl(x.n); return; }
    openModal(x);
  });
  el.addEventListener('keydown',function(ev){
    if(ev.key==='Enter'||ev.key===' '){ ev.preventDefault(); openModal(x); }
  });
  return el;
}

function spin(append){
  if(!append){ shown=[]; grid.innerHTML=''; }
  var picks=pick(12, shown.map(function(x){return x.n;}));
  if(!picks.length){
    grid.innerHTML='<div class=ngempty>'+(cat==='mine'
      ? 'Type a name in the box above and spin again. We will make it a problem.'
      : 'You have seen this whole category. Try another vibe.')+'</div>';
    return;
  }
  picks.forEach(function(x,i){
    var c=card(x); c.style.animationDelay=(i*35)+'ms'; grid.appendChild(c);
  });
  shown=shown.concat(picks);
  $('#ngcount').textContent=shown.length+' shown · '+pool(cat).length+' in this bucket';
  if(!append && grid.getBoundingClientRect().top<0){
    window.scrollTo({top: grid.offsetTop-70, behavior:'smooth'});
  }
}

function toggleSave(n){
  var i=saved.indexOf(n);
  if(i>-1) saved.splice(i,1); else saved.push(n);
  try{ localStorage.setItem('bns_saved',JSON.stringify(saved)); }catch(e){}
  document.querySelectorAll('.ngcard').forEach(function(c){
    var b=c.querySelector('.sv'), s=saved.indexOf(c.dataset.n)>-1;
    b.textContent=s?'♥':'♡'; b.classList.toggle('saved',s);
  });
  renderSaved(); toast(i>-1?'Removed':'Saved');
}
function renderSaved(){
  $('#ngtray').hidden = !saved.length;
  $('#ngsaved').innerHTML = saved.map(function(n){
    return '<span class=ngsv>'+esc(n)+' <button type=button data-n="'+esc(n)
         + '" aria-label="Remove">×</button></span>';
  }).join('');
  $('#ngsaved').querySelectorAll('button').forEach(function(b){
    b.onclick=function(){ toggleSave(b.dataset.n); };
  });
}
function copy(t,msg){
  var p = navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject();
  p.then(function(){ toast(msg||'Copied'); })
   .catch(function(){ toast('Select and copy manually'); });
}
var tt; function toast(m){
  var t=$('#ngtoast'); t.textContent=m; t.classList.add('show');
  clearTimeout(tt); tt=setTimeout(function(){ t.classList.remove('show'); },1400);
}

/* ---- modal ---- */
var lastFocus=null;
function openModal(x){
  cur=x; lastFocus=document.activeElement;
  $('#ngmname').textContent=x.n;
  $('#ngmnote').textContent=x.note||label(x.cat);
  $('#ngttxt').textContent=x.n;
  $('#ngtport').textContent=port.value.trim();
  $('#ngmradio').textContent='"Mayday, mayday, mayday. This is '+x.n+', '+x.n+', '
    + x.n+'." Say it out loud. Could you say it to the Coast Guard in front of '
    + 'your family?';
  var r=radio(x.n), f=fitw(x.n), L=letters(x.n), w=x.n.trim().split(/\s+/).length;
  $('#ngmtests').innerHTML=
    '<div class=ngtest><b>Radio call</b>'+r[1].replace('Radio: ','')+' — '+L
      +' letters, '+w+' word'+(w>1?'s':'')+'</div>'
   +'<div class=ngtest><b>Transom width at 4" tall</b>'+f[1]+' (approx.)</div>'
   +'<div class=ngtest><b>Spell test</b>'
     +(/[^A-Za-z\s']/.test(x.n)?'Has symbols or numbers — you will be spelling this one'
                               :'Phonetic enough. Good.')+'</div>'
   +'<div class=ngtest><b>Uniqueness</b>'
     +(['classy','fishing'].indexOf(x.cat)>-1?'Check your marina first'
                                             :'You will not meet another one of these')+'</div>';
  $('#ngmsave').textContent = saved.indexOf(x.n)>-1 ? 'Saved ♥' : 'Save';
  $('#ngmcut').href=cutUrl(x.n);
  $('#ngmodal').classList.add('open');
  document.body.style.overflow='hidden';
  $('#ngclose').focus();
}
function closeModal(){
  $('#ngmodal').classList.remove('open');
  document.body.style.overflow='';
  if(lastFocus && lastFocus.focus) lastFocus.focus();
}
$('#ngclose').onclick=closeModal;
$('#ngmodal').addEventListener('click',function(e){
  if(e.target.id==='ngmodal') closeModal();
});
$('#ngmsave').onclick=function(){
  toggleSave(cur.n);
  $('#ngmsave').textContent = saved.indexOf(cur.n)>-1 ? 'Saved ♥' : 'Save';
};
$('#ngmcopy').onclick=function(){ copy(cur.n); };
$('#ngmshare').onclick=function(){
  var u=location.origin+location.pathname+'?n='+encodeURIComponent(cur.n);
  if(navigator.share){ navigator.share({title:'Boat name: '+cur.n, text:cur.n, url:u})
    .catch(function(){}); }
  else copy(u,'Link copied');
};
$('#ngfonts').querySelectorAll('button').forEach(function(b){
  b.style.fontFamily=b.dataset.css;
  b.onclick=function(){
    var on=$('#ngfonts .on'); if(on) on.classList.remove('on');
    b.classList.add('on');
    $('#ngttxt').style.fontFamily=b.dataset.css;
  };
});
$('#ngttxt').style.fontFamily=$('#ngfonts button').dataset.css;
document.querySelectorAll('.ngcolors button').forEach(function(b){
  b.onclick=function(){
    $('#ngttxt').style.color=b.dataset.c;
    $('#ngtport').style.color=b.dataset.c;
  };
});

/* ---- categories ---- */
CATS.forEach(function(c){
  var id=c[0], lab=c[1], hint=c[2];
  var b=document.createElement('button');
  b.type='button';
  b.className='ngcat'+(id==='mine'?' special':'')+(id===cat?' on':'');
  b.dataset.id=id; b.title=hint; b.textContent=lab;
  b.onclick=function(){
    cat=id;
    catsEl.querySelectorAll('.ngcat').forEach(function(x){
      x.classList.toggle('on', x.dataset.id===id);
    });
    if(id==='mine' && !who.value.trim()){ who.focus(); toast('Type a name first'); }
    spin(false);
  };
  catsEl.appendChild(b);
});
who.addEventListener('input',function(){
  var b=catsEl.querySelector('[data-id="mine"]');
  if(b) b.classList.toggle('armed', !!who.value.trim());
});
who.addEventListener('keydown',function(e){
  if(e.key==='Enter'){
    cat='mine';
    catsEl.querySelectorAll('.ngcat').forEach(function(x){
      x.classList.toggle('on', x.dataset.id==='mine');
    });
    spin(false);
  }
});
port.addEventListener('input',function(){ $('#ngtport').textContent=port.value.trim(); });

$('#ngspin').onclick=function(){ spin(false); };
$('#ngmore').onclick=function(){ spin(true); };
$('#ngcopyall').onclick=function(){ copy(saved.join('\n'),'List copied'); };
$('#ngclearall').onclick=function(){
  saved=[];
  try{ localStorage.removeItem('bns_saved'); }catch(e){}
  renderSaved();
  document.querySelectorAll('.ngcard .sv').forEach(function(b){
    b.textContent='♡'; b.classList.remove('saved');
  });
};
document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
  var open=$('#ngmodal').classList.contains('open');
  if(e.key==='Escape' && open){ closeModal(); return; }
  if(open) return;
  if(e.code==='Space'){ e.preventDefault(); spin(false); }
  if(e.key==='s'||e.key==='S'){ catsEl.querySelector('[data-id="surprise"]').click(); }
});

renderSaved();
spin(false);
var q=new URLSearchParams(location.search).get('n');
if(q) openModal({n:q, cat:'surprise'});
})();
"""
