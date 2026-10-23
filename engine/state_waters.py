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
    "Islamorada, Marathon and Key West - flats skiffs, centre consoles and the "
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
    "centre of the state's trailer-boat culture."),
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
    "32 miles of clear Adirondack water, and the single most recognisable "
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
    "shared with Arizona, and the centre of the desert performance-boat scene."),
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
    "shoreline counting the tributaries. Crab boats, centre consoles and "
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
    "about 54,000 acres. The most recognisable recreational lake in the "
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
}
