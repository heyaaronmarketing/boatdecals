# -*- coding: utf-8 -*-
"""Where people actually boat, state by state.

Written to answer the question a state page is really being searched for:
"I have a boat in <state> - where does everyone go, and what do I have to
register?" The registration counts and the scope line come from the Coast
Guard (see content.py USCG_* ); this file is the geography.

House rules for the entries below:
  * name the water the way a local names it (Kentucky Lake, not Kentucky
    Reservoir), because that is what gets typed into a search box
  * one concrete reason per water - size, shoreline, what it is known for.
    "Beautiful lake" is worth nothing to a reader or to an answer engine
  * superlatives only where they are defensible, and scoped precisely:
    "largest lake wholly inside Texas" is a different claim from "largest
    lake in Texas", and Toledo Bend is the reason that matters
"""

# slug -> dict(lede, waters=[(name, note)], season)
WATERS = {

 "iowa": dict(
  lede="Iowa boating splits three ways: the natural glacial lakes in the "
       "north-west, the Corps of Engineers reservoirs through the middle, and "
       "the two big rivers that form both state lines.",
  waters=[
   ("Lake Okoboji and Spirit Lake",
    "the Iowa Great Lakes in Dickinson County, and the busiest recreational "
    "water in the state. West Okoboji is a true blue-water glacial lake and "
    "the summer traffic shows it."),
   ("Clear Lake",
    "3,600 acres in Cerro Gordo County, shallow, windy and a sailing and "
    "pontoon lake more than a ski lake."),
   ("Rathbun Lake",
    "around 11,000 acres near Centerville, the largest lake in southern Iowa "
    "and the one people trailer to for a long weekend."),
   ("Saylorville and Red Rock",
    "the Des Moines River reservoirs, close enough to the metro that they take "
    "the weekday evening traffic."),
   ("Coralville Lake",
    "the eastern Iowa reservoir above Iowa City, with the Corps campgrounds "
    "that fill up from May."),
   ("The Mississippi and the Missouri",
    "both state borders are navigable river. Pool boating on the Mississippi "
    "around Dubuque, Guttenberg and the Quad Cities is a whole scene of its "
    "own, and the lock system means you share water with commercial tows."),
  ],
  season="Ice-out is usually late March to mid-April and most boats are out of "
         "the water by the end of October. The practical season is about six "
         "months, which is why spring re-lettering is such a rush here."),

 "florida": dict(
  lede="Florida is the biggest boating state in the country by registrations, "
       "and almost none of it is lake boating. The fleet lives on salt water, "
       "the Intracoastal and the big inland rivers.",
  waters=[
   ("Lake Okeechobee",
    "about 730 square miles, the largest freshwater lake in Florida and the "
    "second largest wholly inside the lower 48. Shallow, famous for bass, and "
    "a route across the state via the Okeechobee Waterway."),
   ("The Intracoastal Waterway",
    "runs the length of both coasts. For a huge share of Florida owners the "
    "ICW is the home water, not any named lake."),
   ("The Florida Keys",
    "Islamorada, Marathon and Key West - flats skiffs, center consoles and the "
    "heaviest sport-fishing concentration in the state."),
   ("Tampa Bay and Charlotte Harbor",
    "the Gulf-coast estuaries, with Boca Grande Pass as the tarpon address "
    "every spring."),
   ("The St. Johns River",
    "310 navigable miles running north, one of very few major US rivers that "
    "does. Jacksonville to Sanford is cruising water."),
   ("Biscayne Bay and the Miami River",
    "the busiest small-boat water in the south-east, and the one with the "
    "tightest enforcement."),
  ],
  season="Year round. Florida does not have a boating season, it has a "
         "hurricane season - June through November - and that is what dictates "
         "when boats get hauled."),

 "michigan": dict(
  lede="Michigan touches four of the five Great Lakes and has around 11,000 "
       "inland lakes behind them. No state has more coastline outside Alaska.",
  waters=[
   ("Lake Michigan",
    "the west coast, from New Buffalo up through Holland, Muskegon and the "
    "Leelanau Peninsula. Big-water boating that demands a real forecast check."),
   ("Lake St. Clair",
    "between Detroit and Ontario - shallow, warm and one of the densest "
    "recreational fleets in the Midwest. Muskie capital, and a serious "
    "poker-run scene."),
   ("Houghton Lake",
    "just over 20,000 acres, the largest inland lake in Michigan, and the "
    "center of the state's trailer-boat culture."),
   ("Torch Lake and the Chain of Lakes",
    "Antrim County - 19 miles long, deep, and the postcard water everyone "
    "photographs."),
   ("Grand Traverse Bay",
    "Traverse City as the base, protected enough for a small boat and open "
    "enough to feel like the big lake."),
   ("Lake Superior and the Keweenaw",
    "the cold end. Short season, serious water, and the Apostle- and "
    "Isle-Royale-bound crowd."),
  ],
  season="Inland lakes run roughly May to October. The Great Lakes season is "
         "shorter at the north end and ice can hold into April on Superior."),

 "new-york": dict(
  lede="New York runs from ocean inlets to alpine lakes, joined by a canal "
       "system you can still legally cross the state on.",
  waters=[
   ("Lake George",
    "32 miles of clear Adirondack water, and the single most recognizable "
    "recreational boating address in the state."),
   ("The Finger Lakes",
    "Seneca and Cayuga are the long deep ones; Canandaigua and Keuka carry the "
    "day-boat traffic. Wine country on the shoreline is half the draw."),
   ("Lake Champlain",
    "shared with Vermont, 120 miles long, and big enough to need respect."),
   ("The Thousand Islands",
    "the St. Lawrence between Clayton and Alexandria Bay - the wooden-boat "
    "heartland of the north-east."),
   ("Lake Ontario and the Erie Canal",
    "the canal still connects the Hudson to the Great Lakes, and the Loop "
    "crowd uses it every season."),
   ("Long Island Sound and the Great South Bay",
    "the salt-water fleet, from Montauk charter boats to Fire Island runabouts."),
  ],
  season="May through October for most of the state. The Erie Canal navigation "
         "season is set annually and typically runs mid-May to mid-October."),

 "california": dict(
  lede="California calls them CF numbers, not registration numbers, and the "
       "boating divides sharply between the Delta, the big reservoirs and the "
       "coast.",
  waters=[
   ("Lake Tahoe",
    "1,645 feet deep, straddling the Nevada line, and the most photographed "
    "boating water in the West."),
   ("The Sacramento-San Joaquin Delta",
    "around 1,000 miles of navigable sloughs and channels. For a big part of "
    "the Northern California fleet this is the home water."),
   ("Lake Shasta and Lake Oroville",
    "the houseboat reservoirs. Shasta has over 350 miles of shoreline when "
    "it is full, and the water level is the whole conversation."),
   ("Lake Havasu and the lower Colorado",
    "shared with Arizona, and the center of the desert performance-boat scene."),
   ("Clear Lake",
    "the largest natural freshwater lake entirely inside California, and a "
    "national-calibre bass fishery."),
   ("San Francisco Bay",
    "serious sailing water - wind, tide and commercial traffic all at once."),
  ],
  season="Year round on the coast and in the south. The Sierra reservoirs run "
         "roughly April to October and the level depends entirely on snowpack."),

 "south-carolina": dict(
  lede="South Carolina registers all watercraft, and between the Santee Cooper "
       "lakes, the upstate reservoirs and the Lowcountry salt water there is "
       "somewhere to use them year round.",
  waters=[
   ("Lake Murray",
    "about 50,000 acres outside Columbia, with roughly 650 miles of shoreline. "
    "The state's busiest recreational lake."),
   ("Lakes Marion and Moultrie",
    "the Santee Cooper system - around 170,000 acres between them, flooded "
    "cypress and the fishery that made the state's reputation."),
   ("Lake Hartwell",
    "on the Georgia line, 56,000 acres and a regular stop on the national "
    "bass circuits."),
   ("Lake Keowee",
    "clear, deep, mountain-fed water in the upstate - the swimming and "
    "wakeboarding lake rather than the fishing one."),
   ("The Intracoastal Waterway",
    "Little River down to Beaufort, with Charleston Harbor as the hub."),
   ("Winyah Bay and the Waccamaw",
    "blackwater rivers running to the coast around Georgetown."),
  ],
  season="Effectively year round. The heavy season is April through October, "
         "and the upstate lakes stay usable through a mild winter."),

 "wisconsin": dict(
  lede="Wisconsin has two Great Lakes coasts, roughly 15,000 inland lakes and "
       "a border river, and registers everything motorised plus sailboats "
       "over 12 feet.",
  waters=[
   ("Lake Winnebago",
    "137,700 acres, the largest lake entirely inside Wisconsin. Shallow, "
    "quick to build a chop, and the home of the sturgeon season."),
   ("The Madison lakes",
    "Mendota and Monona, in the middle of the city - the densest weekday "
    "small-boat traffic in the state."),
   ("Lake Geneva",
    "the Chicago-money lake in Walworth County, and the busiest summer "
    "shoreline in southern Wisconsin."),
   ("Door County and Green Bay",
    "Sturgeon Bay as the base, with the ship canal connecting bay to lake."),
   ("The Apostle Islands",
    "Lake Superior off Bayfield - sea kayaks, sailboats and short seasons."),
   ("The Chain O'Lakes at Waupaca",
    "22 connected lakes you can run all day without trailering."),
  ],
  season="Roughly May through October inland. Ice-out on the northern lakes "
         "can run into late April, and ice fishing takes over the rest."),

 "minnesota": dict(
  lede="Land of 10,000 Lakes undersells it - the state counts 11,842 lakes "
       "over ten acres. Per head, Minnesota owns more boats than anywhere "
       "else in the country.",
  waters=[
   ("Lake Minnetonka",
    "14,000 acres west of Minneapolis, 125 miles of shoreline, and the "
    "busiest recreational lake in the state."),
   ("Mille Lacs",
    "132,000 acres, big enough to make its own weather, and a walleye "
    "destination with its own regulation history."),
   ("Leech Lake and Lake Winnibigoshish",
    "the big north-central water around Walker and Bena."),
   ("Lake Vermilion",
    "40,000 acres with 365 islands, up on the Iron Range."),
   ("Lake of the Woods",
    "the far north - partly Canadian, 14,552 islands, and a serious crossing "
    "in weather."),
   ("Lake Superior and the North Shore",
    "Duluth out to Grand Marais, the coldest and least forgiving water in "
    "the state."),
  ],
  season="Ice-out runs from early April in the south to early May up north, "
         "and the Minnesota fishing opener in mid-May is the real start. Most "
         "boats are out by the end of October."),

 "texas": dict(
  lede="Texas is nearly all reservoir boating - there is only one large "
       "natural lake in the state - plus 367 miles of Gulf coast.",
  waters=[
   ("Sam Rayburn Reservoir",
    "114,500 acres, the largest lake wholly inside Texas, and a permanent "
    "fixture on the tournament calendar."),
   ("Toledo Bend",
    "181,600 acres shared with Louisiana, which makes it bigger than Rayburn "
    "but not a Texas lake on its own."),
   ("Lake Texoma",
    "on the Oklahoma line, striper water, and one of the few Corps lakes with "
    "real marina infrastructure on both shores."),
   ("Lake Travis and Lake Austin",
    "the Highland Lakes chain on the Colorado River. Travis is the party "
    "lake; Austin is the no-wake one."),
   ("Lake Conroe and Lake Livingston",
    "the Houston-area water, close enough for a Saturday."),
   ("Galveston Bay and the Laguna Madre",
    "the salt-water fleet - bay boats north, shallow-draft skiffs south."),
  ],
  season="Year round in practice. Summer heat moves traffic to early morning "
         "and evening, and lake levels in a drought year decide which ramps "
         "are usable."),

 "pennsylvania": dict(
  lede="Pennsylvania is unusual: the Fish & Boat Commission registers "
       "non-powered craft too if you use state lakes or access areas, so "
       "kayaks and canoes are in the count here when they are not elsewhere.",
  waters=[
   ("Raystown Lake",
    "8,300 acres and 118 miles of shoreline, the largest lake entirely inside "
    "Pennsylvania and the state's houseboat water."),
   ("Lake Erie and Presque Isle Bay",
    "the state's only Great Lakes frontage, with Erie as the port and the "
    "steelhead run as the draw."),
   ("Lake Wallenpaupack",
    "5,700 acres in the Poconos, 52 miles of shoreline, and the busiest "
    "recreational lake in the east of the state."),
   ("Pymatuning Reservoir",
    "shared with Ohio, famously restricted to low-horsepower use for decades."),
   ("The Allegheny Reservoir",
    "Kinzua, running up into New York, with deep water and steep sides."),
   ("The three rivers at Pittsburgh",
    "Allegheny, Monongahela and Ohio - urban river boating with locks and "
    "commercial tows."),
  ],
  season="April through October for most of the state. The Commission's "
         "access areas open earlier than the marinas do."),

 "north-carolina": dict(
  lede="North Carolina runs mountain reservoirs on one end and the largest "
       "lagoon system on the US East Coast on the other.",
  waters=[
   ("Lake Norman",
    "over 32,000 acres and 520 miles of shoreline, the largest man-made lake "
    "in the state and the one closest to Charlotte."),
   ("Pamlico and Albemarle Sounds",
    "the biggest lagoon system on the East Coast, shallow, protected and "
    "enormous."),
   ("The Outer Banks and Oregon Inlet",
    "the offshore fleet - Hatteras and Oregon Inlet are the Gulf Stream "
    "access points."),
   ("Lake Gaston and Kerr Lake",
    "on the Virginia line, with Kerr shared between the two states."),
   ("Jordan Lake and Falls Lake",
    "the Triangle's weekday water, close to Raleigh and Durham."),
   ("Fontana and Lake James",
    "the mountain reservoirs in the west, deep and cold."),
  ],
  season="Roughly April through October inland, and the coastal fleet runs "
         "most of the year with the offshore season peaking in summer."),

 "georgia": dict(
  lede="Georgia boating is reservoir boating, concentrated in a ring around "
       "metro Atlanta, plus the Golden Isles on the coast.",
  waters=[
   ("Lake Lanier",
    "38,000 acres north-east of Atlanta, and one of the most visited Corps of "
    "Engineers lakes in the country. Summer weekends are genuinely crowded."),
   ("Clarks Hill Lake",
    "71,000 acres on the South Carolina line, where it is called Thurmond "
    "Lake. The biggest Corps lake east of the Mississippi."),
   ("Lake Oconee and Lake Sinclair",
    "the Milledgeville-to-Greensboro water, warm year round below the dam."),
   ("Lake Allatoona",
    "12,000 acres north-west of Atlanta, closest big water to the city and "
    "busy because of it."),
   ("West Point Lake and Lake Seminole",
    "the Chattahoochee reservoirs, with Seminole on the Florida line."),
   ("The Golden Isles and the ICW",
    "St. Simons, Jekyll and the salt marsh behind them."),
  ],
  season="Year round in the south of the state. The lake season runs hard from "
         "April through October."),

 "virginia": dict(
  lede="Virginia is Chesapeake Bay first and reservoirs second, and the "
       "registration rules follow the motor rather than the hull.",
  waters=[
   ("Chesapeake Bay",
    "the largest estuary in the United States, with more than 11,000 miles of "
    "shoreline counting the tributaries. Crab boats, center consoles and "
    "cruising sailboats all at once."),
   ("Smith Mountain Lake",
    "20,000 acres and 500 miles of shoreline near Roanoke, the state's busiest "
    "inland recreational water."),
   ("Lake Anna",
    "13,000 acres between Richmond and Fredericksburg, with a warm side and a "
    "cold side thanks to the power station."),
   ("Kerr Reservoir",
    "Buggs Island to everyone local - 50,000 acres shared with North Carolina."),
   ("The Potomac and the James",
    "tidal rivers with real boating traffic well inland."),
   ("Virginia Beach and Rudee Inlet",
    "the offshore access point for the sport-fishing fleet."),
  ],
  season="April through October inland. The Bay fleet runs most of the year, "
         "and the striper season extends it at both ends."),

 "ohio": dict(
  lede="Ohio registers all watercraft, which is why its fleet sits so high in "
       "the national count - kayaks and canoes are in the number here.",
  waters=[
   ("Lake Erie",
    "the shallowest and warmest Great Lake, which makes it both the most "
    "productive and the quickest to turn dangerous. The Western Basin around "
    "Port Clinton and the Bass Islands is the busiest."),
   ("Grand Lake St. Marys",
    "13,500 acres, built as a canal feeder and still the largest inland lake "
    "in the state."),
   ("Mosquito Creek and Pymatuning",
    "the north-east reservoirs, with Pymatuning shared with Pennsylvania."),
   ("Alum Creek and Hoover Reservoir",
    "the Columbus weekday lakes."),
   ("Indian Lake",
    "a shallow 5,800-acre lake in Logan County with a long resort history."),
   ("The Ohio River",
    "the whole southern border, locked and navigable, shared with barge "
    "traffic."),
  ],
  season="Roughly late April through October. Lake Erie's walleye run pulls "
         "boats out early, often before the weather deserves it."),

 "illinois": dict(
  lede="Illinois boating is the Chain O'Lakes in the north, the big downstate "
       "reservoirs, and two of the most heavily used rivers in the country.",
  waters=[
   ("The Chain O'Lakes",
    "fifteen connected lakes and the Fox River in Lake and McHenry counties - "
    "the densest recreational boating traffic in Illinois by a wide margin."),
   ("Carlyle Lake",
    "26,000 acres, the largest man-made lake in the state, and a sailing lake "
    "because of the open wind."),
   ("Lake Shelbyville and Rend Lake",
    "the central and southern Corps reservoirs."),
   ("Lake Michigan at Chicago",
    "the harbour system from Montrose down to Jackson Park, and a skyline "
    "view that nothing else matches."),
   ("The Illinois River",
    "Peoria to the Mississippi, locked, commercial and part of the Great Loop."),
   ("The Mississippi",
    "the whole western border, pool by pool."),
  ],
  season="April through October, with ice on the northern lakes most winters."),

 "missouri": dict(
  lede="Missouri boating means the Ozark reservoirs, and the shorelines are "
       "far longer than the surface areas suggest.",
  waters=[
   ("Lake of the Ozarks",
    "roughly 1,150 miles of shoreline - more than the California coast - on "
    "about 54,000 acres. The most recognizable recreational lake in the "
    "Midwest and a genuine party water."),
   ("Table Rock Lake",
    "43,000 acres near Branson, clear and deep, and the serious bass lake of "
    "the three."),
   ("Truman Lake",
    "55,000 acres and the largest surface area in the state, timber-filled "
    "and quieter than the Ozarks."),
   ("Bull Shoals",
    "shared with Arkansas, steep-sided and deep."),
   ("Mark Twain Lake",
    "the north-east Missouri reservoir, close to Hannibal."),
   ("The Missouri and Mississippi",
    "both navigable, both commercial, and both unforgiving of a small boat "
    "in current."),
  ],
  season="March through November at the Ozarks, with the hard season April "
         "through October."),

 "washington": dict(
  lede="Washington is a salt-water state with an inland-sea problem: Puget "
       "Sound has tides, currents and commercial traffic that behave nothing "
       "like a lake.",
  waters=[
   ("Puget Sound",
    "the inland sea, from Olympia to Bellingham. Tides run hard through the "
    "passes and a chart is not optional."),
   ("The San Juan Islands",
    "172 named islands, and the single most popular cruising ground in the "
    "Pacific Northwest."),
   ("Lake Washington and Lake Union",
    "Seattle's home water, joined to the Sound by the Ballard Locks."),
   ("Lake Chelan",
    "55 miles long and 1,486 feet deep - the third deepest lake in the "
    "United States."),
   ("Lake Roosevelt",
    "130 miles of the Columbia behind Grand Coulee, and the state's houseboat "
    "water."),
   ("The Columbia River",
    "the Oregon border, locked and navigable far inland."),
  ],
  season="Year round on the Sound for the hardy; the real season is May "
         "through September. East-side lakes freeze."),

 "louisiana": dict(
  lede="Louisiana boating is estuary and swamp more than lake, and the "
       "registration scope reflects a state where almost everyone has a boat.",
  waters=[
   ("Lake Pontchartrain",
    "630 square miles of brackish estuary at New Orleans' back door, crossed "
    "by a 24-mile causeway."),
   ("Toledo Bend",
    "181,600 acres on the Texas line, the largest man-made water body in the "
    "South."),
   ("The Atchafalaya Basin",
    "the largest wetland and swamp in the United States - a million acres of "
    "it, and a different kind of boating entirely."),
   ("Caddo Lake",
    "the bald cypress maze on the Texas border, and one of very few natural "
    "lakes in the state."),
   ("Venice and Grand Isle",
    "the offshore jump-off points, with the Mississippi birdfoot delta in "
    "between."),
   ("The Mississippi River",
    "the whole length of the state, deep-draft commercial all the way to "
    "Baton Rouge."),
  ],
  season="Year round. Hurricane season from June to November is what actually "
         "governs when boats come out of the water."),

 "alabama": dict(
  lede="Alabama has more navigable inland waterway than almost any other "
       "state, most of it the dammed Tennessee and Coosa rivers, plus the "
       "Gulf at the bottom.",
  waters=[
   ("Lake Guntersville",
    "69,000 acres, the largest lake in Alabama, and one of the best-known "
    "bass fisheries in the country."),
   ("Lewis Smith Lake",
    "21,000 acres, deep and clear, with 500 miles of shoreline in the "
    "Bankhead forest."),
   ("Wheeler and Wilson Lakes",
    "the Tennessee River chain across the north of the state."),
   ("Lay, Logan Martin and Neely Henry",
    "the Coosa River chain through the middle - the weekend water for "
    "Birmingham."),
   ("Mobile Bay and the Delta",
    "the second largest river delta system in the country behind the "
    "Mississippi."),
   ("Gulf Shores and Orange Beach",
    "the offshore fleet, and one of the largest artificial reef zones in "
    "the Gulf."),
  ],
  season="Effectively year round, with the hard season March through "
         "November."),

 "tennessee": dict(
  lede="Tennessee is a dammed-river state: the TVA system means there is big "
       "water within an hour of almost anywhere.",
  waters=[
   ("Kentucky Lake",
    "160,000 acres shared with Kentucky, the largest man-made lake east of "
    "the Mississippi, joined to Lake Barkley by a canal."),
   ("Norris Lake",
    "34,000 acres and 800 miles of shoreline north of Knoxville - clean, "
    "deep and the houseboat lake."),
   ("Dale Hollow",
    "shared with Kentucky, and famous for water clarity."),
   ("Center Hill and Old Hickory",
    "the Nashville-area lakes, with Percy Priest closest to the city."),
   ("Chickamauga and Watts Bar",
    "the Chattanooga and east Tennessee river lakes."),
   ("The Tennessee River",
    "running across the state twice, locked the whole way."),
  ],
  season="March through November, with the TVA drawdown lowering lake levels "
         "through the winter."),

 "indiana": dict(
  lede="Indiana registers motorised boats used on public water, and the "
       "boating divides between the northern natural lakes, the southern "
       "reservoirs and a short strip of Lake Michigan.",
  waters=[
   ("Lake Monroe",
    "10,750 acres south of Bloomington, the largest lake inside Indiana."),
   ("Lake Wawasee",
    "the largest natural lake in the state, in Kosciusko County, where the "
    "glacial lake country starts."),
   ("Patoka Lake",
    "8,800 acres in the south, the second largest and the quieter one."),
   ("Geist and Morse Reservoirs",
    "the Indianapolis weekday water."),
   ("Lake Michigan at Michigan City",
    "a short coast, but a real port and a charter fleet."),
   ("The Ohio River",
    "the southern border, locked and navigable."),
  ],
  season="Roughly late April through October, with ice on the northern lakes."),
 "mississippi": dict(
   lede="Mississippi boating is three different sports: the flood-control lakes in "
        "the hills, one big reservoir in the middle of the state, and salt water on "
        "the Sound.",
   waters=[
     ("Ross Barnett Reservoir",
      "the Jackson lake, impounded on the Pearl River and the busiest recreational "
      "water in the state - it is where most of the central-Mississippi fleet lives."),
     ("Sardis, Enid, Grenada and Arkabutla",
      "the four Corps of Engineers flood-control lakes along the hill country. Their "
      "levels swing hard with the season, which is why the ramps move."),
     ("Pickwick Lake",
      "shared with Tennessee and Alabama in the north-east corner, and the deepest "
      "water in the state."),
     ("The Mississippi Sound and the barrier islands",
      "Biloxi, Gulfport, Pass Christian and the run out to Ship and Horn Islands. "
      "Salt, tide and commercial traffic - a different kind of boating entirely."),
     ("The Mississippi River",
      "the whole western border, and working water rather than recreational for most "
      "of its length."),
   ],
   season="Year-round on the coast. The reservoirs quieten from December through "
          "February but never freeze."),
 "maine": dict(
   lede="Maine registers boats for inland OR tidal water and charges differently for "
        "each, which tells you how the state thinks about its own geography.",
   waters=[
     ("Sebago Lake",
      "the deepest lake in the state and the closest big water to Portland, which "
      "makes it the busiest."),
     ("Moosehead Lake",
      "the largest lake wholly inside Maine, and remote enough that the boating "
      "season is genuinely short."),
     ("The Belgrade Lakes",
      "Great Pond, Long Pond and their neighbours in Kennebec County - camp country, "
      "and a lot of small outboards."),
     ("The Rangeley Lakes",
      "the western mountains chain, cold and deep."),
     ("Casco Bay and Penobscot Bay",
      "the two great island-studded bays. This is where the tidal-only registration "
      "rate earns its keep."),
   ],
   season="Short and intense. Ice-out on the big inland lakes is usually late April "
          "into May, and the inland season is effectively over by October."),
 "arkansas": dict(
   lede="Arkansas is reservoir country - the Corps and the power companies dammed "
        "the Ozark and Ouachita rivers, and the results are some of the clearest "
        "water in the South.",
   waters=[
     ("Lake Ouachita",
      "the largest lake wholly inside Arkansas, and undeveloped enough around its "
      "shoreline that it stays clear."),
     ("Beaver Lake and Bull Shoals",
      "the White River impoundments in the north-west, with Bull Shoals shared with "
      "Missouri."),
     ("Greers Ferry Lake",
      "two basins joined by a narrow neck near Heber Springs, and a long-standing "
      "clear-water reputation."),
     ("Lake Dardanelle",
      "the Arkansas River navigation pool at Russellville, and a regular tournament "
      "stop."),
     ("DeGray Lake",
      "a Caddo River impoundment south-west of Hot Springs."),
     ("The White River",
      "tailwater below Bull Shoals - cold, fast and a trout fishery rather than a "
      "ski run."),
   ],
   season="Long. The reservoirs stay open all year and the spring tournament season "
          "starts early."),
 "massachusetts": dict(
   lede="Massachusetts registers only boats with a motor, which is why its fleet "
        "number looks small next to its coastline - the whole sailing and paddling "
        "world is outside the count.",
   waters=[
     ("Cape Cod Bay and Buzzards Bay",
      "the two bodies either side of the Cape, and between them the bulk of the "
      "state's salt-water boating."),
     ("Boston Harbor and the Harbor Islands",
      "a working harbour with a national park inside it."),
     ("Nantucket Sound",
      "the water between the Cape, Martha's Vineyard and Nantucket, and some of the "
      "busiest ferry traffic in New England."),
     ("Lake Quinsigamond",
      "the long narrow lake on the Worcester line, and a rowing course since the "
      "19th century."),
     ("The Merrimack River",
      "tidal from Haverhill down to Newburyport, and busy both ways."),
   ],
   season="Salt-water season runs from the spring haul-out through to October. "
          "Inland lakes freeze."),
 "new-jersey": dict(
   lede="New Jersey packs a lot of boating into a small state: barrier-island bays "
        "down the whole shore, two tidal rivers, and the glacial lakes up in the "
        "north-west.",
   waters=[
     ("Barnegat Bay",
      "the long shallow bay behind Long Beach Island, and the centre of gravity for "
      "Jersey Shore boating."),
     ("Raritan Bay and Sandy Hook",
      "the northern salt water, with New York Harbor traffic on the far side."),
     ("Lake Hopatcong",
      "the largest lake in New Jersey, up in Morris and Sussex Counties."),
     ("The Delaware River",
      "the entire western border, tidal from Trenton south and non-tidal above it."),
     ("Greenwood Lake",
      "straddling the New York state line, which means two sets of rules on one "
      "body of water."),
     ("Round Valley Reservoir",
      "the deepest water in the state, and cold enough to stay clear."),
   ],
   season="Shore season runs Memorial Day to Columbus Day, with the serious fishing "
          "fleet out either side of it."),
 "oregon": dict(
   lede="Oregon wants a boat registered whenever it is on the water at all, moored "
        "at the dock included - which is worth knowing before you leave one on a "
        "slip over the winter.",
   waters=[
     ("The Columbia River",
      "the whole northern border, and the biggest boating water in the state. "
      "Registration is reciprocal with Washington on it, but the fish rules are not."),
     ("The Willamette River",
      "navigable from Portland up past Salem, and the weekday water for most of the "
      "state's population."),
     ("Detroit Lake and Green Peter",
      "the Santiam reservoirs in the Cascade foothills."),
     ("Crane Prairie and Wickiup",
      "the high Deschutes reservoirs south-west of Bend, with a short season and "
      "cold water."),
     ("The Oregon Coast",
      "Tillamook, Yaquina and Coos Bays, plus the bar crossings that make Oregon "
      "coastal boating its own discipline."),
     ("Lake Billy Chinook",
      "three arms of three rivers in a canyon near Culver."),
   ],
   season="Coastal and Columbia boating runs all year. The Cascade reservoirs are "
          "drawn down over winter and some ramps go dry."),
 "nebraska": dict(
   lede="Nebraska is reservoir and river country, and registration goes through the "
        "county treasurer rather than through Game and Parks.",
   waters=[
     ("Lake McConaughy",
      "\"Big Mac\" on the North Platte near Ogallala - the largest reservoir in the "
      "state and the one with the sand beaches."),
     ("The Missouri River",
      "the entire eastern border, with the Gavins Point and Lewis and Clark stretch "
      "at the top shared with South Dakota."),
     ("Harlan County Lake",
      "a Corps reservoir in the south-central counties, big enough for weather to "
      "build on it."),
     ("Branched Oak and Pawnee",
      "the Lincoln-area Salt Valley lakes, close in and busy."),
     ("Lake Minatare and the North Platte lakes",
      "panhandle water, with the lighthouse at Minatare that has no business being "
      "in Nebraska."),
   ],
   season="Ice in and out. The season is effectively April through October."),
 "idaho": dict(
   lede="Idaho boating divides at the Salmon River: big deep glacial lakes in the "
        "panhandle, reservoirs and the Snake in the south.",
   waters=[
     ("Lake Coeur d'Alene",
      "the panhandle's centrepiece, 25 miles long with the city at the top of it."),
     ("Lake Pend Oreille",
      "the largest lake in Idaho and one of the deepest in the country - the Navy "
      "tests submarine models in it."),
     ("Priest Lake",
      "the quieter northern lake, with the Thorofare running up to the Upper Lake."),
     ("Lake Cascade and Payette Lake",
      "the mountain lakes above Boise, and where the valley goes in summer."),
     ("The Snake River and Hells Canyon",
      "the western border, with jet-boat water in the deepest river gorge in North "
      "America."),
     ("American Falls Reservoir",
      "the big flat-water reservoir on the Snake in the south-east."),
   ],
   season="Short in the mountains, longer on the Snake. The panhandle lakes stay "
          "cold enough to matter all year."),
 "utah": dict(
   lede="Utah charges one flat registration fee whatever you own, which is unusual - "
        "and its two decals go in a specific order on the hull, which is more "
        "unusual still.",
   waters=[
     ("Lake Powell",
      "shared with Arizona, and nearly 2,000 miles of shoreline at full pool. The "
      "water level has moved so much in the last decade that ramps open and close "
      "with it."),
     ("Bear Lake",
      "on the Idaho line, and turquoise from suspended carbonate rather than from "
      "anything in the sky."),
     ("Flaming Gorge Reservoir",
      "shared with Wyoming, deep and cold on the Green River."),
     ("Utah Lake",
      "big, shallow and warm, right beside the Provo population."),
     ("Jordanelle and Deer Creek",
      "the Wasatch Back reservoirs, half an hour from Park City."),
     ("The Great Salt Lake",
      "boatable in parts, and hard on everything metal you take onto it."),
   ],
   season="The low-desert water runs all year. The mountain reservoirs ice over."),
 "montana": dict(
   lede="Montana charges once and never again, which is why its fleet number looks "
        "small for a state with this much water - nothing drops off the roll.",
   waters=[
     ("Flathead Lake",
      "the largest natural freshwater lake west of the Mississippi, and the centre "
      "of Montana boating."),
     ("Fort Peck Lake",
      "134 miles of reservoir on the Missouri in the eastern prairie, with more "
      "shoreline than California's coast."),
     ("Canyon Ferry Lake",
      "the Helena lake, and the busiest water in the central part of the state."),
     ("Lake Koocanusa",
      "90 miles on the Kootenai, shared with British Columbia."),
     ("The Missouri and the Yellowstone",
      "float and jet-boat water rather than ski water, and the Yellowstone is the "
      "longest undammed river in the lower 48."),
   ],
   season="Short. Ice-out on the big lakes runs into April, and the high country is "
          "done by late September."),
 "colorado": dict(
   lede="Colorado boating happens at altitude, which changes the water, the weather "
        "and how an outboard behaves - and the state bands its fees at 20 and 30 "
        "feet rather than the usual 16 and 26.",
   waters=[
     ("Lake Granby and Grand Lake",
      "the headwaters lakes on the west side of Rocky Mountain National Park. Grand "
      "Lake is the largest natural lake in the state."),
     ("Blue Mesa Reservoir",
      "the largest body of water in Colorado, on the Gunnison in the Curecanti "
      "recreation area."),
     ("Chatfield, Cherry Creek and Aurora",
      "the Denver metro reservoirs, close enough for a weekday evening."),
     ("Navajo Reservoir",
      "in the south-west, shared with New Mexico."),
     ("Horsetooth Reservoir",
      "the long narrow reservoir on the hogback above Fort Collins."),
     ("Lake Pueblo",
      "the big warm-water reservoir on the Arkansas, and the longest season in the "
      "state."),
   ],
   season="Short and altitude-dependent. The high reservoirs ice over; Pueblo and "
          "the plains lakes run most of the year."),
 "maryland": dict(
   lede="The Chesapeake is the largest estuary in the United States and the reason "
        "Maryland's fleet is what it is - most of this boating is brackish, tidal "
        "and in sight of a working waterman.",
   waters=[
     ("The Chesapeake Bay",
      "200 miles of it, with Maryland holding the upper two thirds. Everything else "
      "on this list is a tributary of it."),
     ("The Eastern Shore rivers",
      "the Choptank, the Chester, the Wye and the Miles - deep, protected and the "
      "reason Maryland has so many small marinas."),
     ("The Potomac River",
      "the southern border, tidal up to Washington."),
     ("Deep Creek Lake",
      "the one big freshwater lake, up in Garrett County in the Alleghenies, and a "
      "completely different kind of boating."),
     ("The Atlantic at Ocean City",
      "the inlet, the back bays and the offshore canyons beyond them."),
   ],
   season="Year-round on the Bay for the hardy; the main season runs April to "
          "November. Deep Creek freezes."),
 "kentucky": dict(
   lede="Kentucky has more navigable miles than any state but Alaska, and the two "
        "big western lakes are among the largest man-made bodies of water in the "
        "country.",
   waters=[
     ("Kentucky Lake and Lake Barkley",
      "the Tennessee and the Cumberland impounded side by side, joined by a canal, "
      "with Land Between the Lakes down the middle. Kentucky Lake is the larger of "
      "the two and runs well into Tennessee."),
     ("Lake Cumberland",
      "101 miles of reservoir in the south-central counties, and the houseboat "
      "capital of the country by most counts."),
     ("Dale Hollow Lake",
      "shared with Tennessee, and clear enough to see the bottom in 20 feet."),
     ("The Ohio River",
      "the entire northern border, locked and commercially navigable the whole way."),
     ("Laurel River Lake and Cave Run",
      "the clear-water eastern lakes in the Daniel Boone National Forest."),
   ],
   season="Long. The western lakes run most of the year and the houseboat season "
          "starts early."),
 "kansas": dict(
   lede="Kansas has almost no natural lakes, so nearly all of this boating happens "
        "on Corps of Engineers and state reservoirs built in the middle of the 20th "
        "century.",
   waters=[
     ("Milford Lake",
      "the largest lake in Kansas, on the Republican River near Junction City."),
     ("Tuttle Creek Lake",
      "the long reservoir above Manhattan, and big enough to build real weather."),
     ("Perry and Clinton Lakes",
      "the Lawrence and Topeka reservoirs, and the closest water to the "
      "north-eastern population."),
     ("Cheney Reservoir",
      "Wichita's lake, and a serious sailing water because the wind is relentless."),
     ("El Dorado Lake",
      "a Walnut River reservoir in the Flint Hills."),
     ("The Kansas and Missouri Rivers",
      "the Missouri forms the north-eastern border and is commercially navigable."),
   ],
   season="April through October. The reservoirs ice over in a hard winter."),
 "new-hampshire": dict(
   lede="New Hampshire has 18 miles of coast and a great many lakes, and from 2025 "
        "a registered boat carries two decals a side rather than one.",
   waters=[
     ("Lake Winnipesaukee",
      "the largest lake in the state at 44,586 acres, with 253 islands in it. Most "
      "New Hampshire boating happens here."),
     ("Lake Winnisquam and Squam Lake",
      "the two next-largest in the Lakes Region, with Squam quieter by local custom."),
     ("Newfound Lake",
      "small, very deep and famously clear."),
     ("Lake Sunapee",
      "the western lake, with the state's second-busiest fleet."),
     ("The Piscataqua River and the Isles of Shoals",
      "the short, ferocious coast. The Piscataqua runs one of the fastest tidal "
      "currents on the east coast."),
   ],
   season="Short. Ice-out on Winnipesaukee is usually mid-to-late April and the "
          "season closes with the fall haul-out."),
 "delaware": dict(
   lede="Delaware is small, tidal and almost entirely estuary - the Bay on one side, "
        "the Inland Bays on the other, and not much in between.",
   waters=[
     ("Delaware Bay",
      "the whole western shore of it, with Lewes and the Delaware Breakwater at the "
      "mouth."),
     ("Indian River Bay and Rehoboth Bay",
      "the Inland Bays behind the resort coast, shallow and busy all summer."),
     ("The Delaware River",
      "the northern border above the Bay, and commercial water past Wilmington."),
     ("The Chesapeake and Delaware Canal",
      "a working ship canal across the top of the state, and a shortcut between two "
      "of the biggest estuaries in the country."),
     ("Lums Pond and the millponds",
      "the small inland freshwater, which is most of what Delaware has of it."),
   ],
   season="Long on the Bay; the Inland Bays season is Memorial Day to October."),
 "oklahoma": dict(
   lede="Oklahoma has more man-made shoreline than almost anywhere - the Corps "
        "dammed nearly every river in the state - and it charges for a boat on what "
        "the boat is worth rather than how long it is.",
   waters=[
     ("Grand Lake o' the Cherokees",
      "the north-eastern lake on the Neosho, and the busiest recreational water in "
      "the state."),
     ("Lake Texoma",
      "shared with Texas on the Red River, and one of the largest reservoirs in the "
      "country."),
     ("Lake Eufaula",
      "the largest lake wholly inside Oklahoma, on the Canadian River."),
     ("Broken Bow Lake",
      "clear, deep and in the pines of the south-east corner."),
     ("Keystone and Oologah",
      "the Tulsa-area reservoirs."),
     ("Lake Tenkiller",
      "clear-water scuba country on the Illinois River."),
   ],
   season="Long. The southern lakes run most of the year and the season starts in "
          "March."),
 "alaska": dict(
   lede="Alaska registers on one question - does it have a motor - and charges less "
        "for three years than most states charge for one. The water is the reason "
        "the rest of the rules are strict.",
   waters=[
     ("Prince William Sound",
      "protected water out of Whittier and Valdez, with glaciers calving into it."),
     ("Kachemak Bay and Cook Inlet",
      "Homer, Seldovia and some of the largest tides in the world - over 25 feet on "
      "a big one."),
     ("The Kenai River",
      "the most heavily fished river in the state, and powerboat traffic to match."),
     ("Southeast and the Inside Passage",
      "Sitka, Juneau, Ketchikan and the protected runs between them."),
     ("Lake Iliamna",
      "the largest lake in Alaska and the eighth largest in the country."),
     ("The Yukon and the Kuskokwim",
      "working rivers, and in much of western Alaska the road network."),
   ],
   season="Short and weather-bound everywhere, and in much of the state the boat is "
          "transport rather than recreation."),
 "new-mexico": dict(
   lede="New Mexico is desert boating: a handful of big reservoirs at altitude, with "
        "sun that is hard on vinyl and water that moves a long way up and down the "
        "bank.",
   waters=[
     ("Elephant Butte Lake",
      "the largest body of water in the state, on the Rio Grande, and the centre of "
      "New Mexico boating."),
     ("Navajo Lake",
      "in the north-west, shared with Colorado."),
     ("Conchas and Ute Lakes",
      "the eastern plains reservoirs, with Ute among the longest in the south-west."),
     ("Heron and El Vado",
      "the cool high-country lakes in Rio Arriba County, with Heron a no-wake "
      "\"quiet waters\" lake."),
     ("Cochiti Lake",
      "close to Albuquerque and Santa Fe, and no-wake by rule."),
   ],
   season="Long at low elevation, shorter in the north. The sun is the thing that "
          "ages lettering here, not the cold."),
 "north-dakota": dict(
   lede="North Dakota has one enormous reservoir and a great many prairie lakes, and "
        "it has priced the invasive-species problem into every registration.",
   waters=[
     ("Lake Sakakawea",
      "the Missouri impounded behind Garrison Dam - 178 miles long and the third "
      "largest man-made lake in the United States by area."),
     ("Devils Lake",
      "a closed basin that has risen dramatically since the 1990s, drowning roads "
      "and trees, and now some of the best perch water in the country."),
     ("Lake Oahe",
      "the upper end of it, shared with South Dakota."),
     ("The Red River of the North",
      "the eastern border, flowing north to Canada."),
     ("Lake Audubon",
      "separated from Sakakawea by a dike, and quieter for it."),
   ],
   season="Hard ice. Open water is roughly May through October, and ice fishing "
          "takes the rest."),
 "vermont": dict(
   lede="Vermont boating is Lake Champlain and then everything else, and the state "
        "lets you buy one year or two.",
   waters=[
     ("Lake Champlain",
      "120 miles of it, shared with New York and Quebec, and the sixth largest lake "
      "in the United States."),
     ("Lake Memphremagog",
      "shared with Quebec, with most of its length over the border."),
     ("Lake Bomoseen",
      "the largest lake entirely inside Vermont."),
     ("Lake Willoughby",
      "a glacial trench between two cliffs in the Northeast Kingdom, and very deep "
      "for its size."),
     ("The Connecticut River",
      "the whole eastern border, with a series of dams and long flat pools behind "
      "them."),
   ],
   season="Ice-out is April. Champlain carries boats into November; the smaller "
          "lakes do not."),
}
