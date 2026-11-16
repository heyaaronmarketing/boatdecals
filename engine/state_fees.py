# -*- coding: utf-8 -*-
"""What each state charges to register a boat, and who to pay.

WHY THIS FILE EXISTS. The competitor whose state pages rank for the generic
term publishes fifty near-identical pages with no fees on them at all. The
blog post that holds an AI Overview citation is a fifty-state table from 2017.
Neither is hard to beat on substance - but only with figures that are right,
because a wrong fee is the one thing a reader or an answer engine can check in
a single click, and getting it wrong costs more trust than omitting it.

THE RULE, AND IT IS HARD:

  Every figure here comes from the STATE'S OWN official page or form, linked
  in `src`. Nothing is copied from a competitor. Nothing is estimated. Nothing
  is carried over from a previous year because it "probably has not changed".

  If a state does not publish a figure where a reader can see it, `fee` is
  None and `fee_note` says so in plain words. An honest "North Carolina does
  not publish this on its registration page" beats a plausible number, and
  verify.py fails the build on a fee without a source.

`verified` is the date a human last read that figure off the source. It is
rendered on the page, so it ages in public - which is the point. Re-read the
sources before touching it.

Fees here are the STATE REGISTRATION FEE only. They are not what we charge;
our price is in content.PRICE. Several states add surcharges, county taxes or
transaction fees that vary - those go in `extra`, never folded into the table,
because a total we invented would be wrong for most readers.
"""

# Everything verified on this date unless a row says otherwise.
VERIFIED = "2026-11-15"

# slug -> {
#   period     how long a registration runs, in the state's own terms
#   rows       [(length band, fee)] exactly as the state publishes them
#   fee        False only when the state publishes no figure (see fee_note)
#   agency     who issues it
#   agency_url the official page a reader should go to
#   src        the official page or form the FIGURES came from
#   src_name   what to call that source on the page
#   extra      charges the state adds that are not a flat part of the table
#   gotcha     the state-specific thing people get wrong
# }
FEES = {
 "florida": {
   "fee_summary": '$28.75 for the common 16-to-26-foot band, from $5.50 for a dinghy to $189.75 for a 110-footer',
   "period": "one year or two years, owner's choice",
   "rows": [("Under 12 ft", "$5.50"), ("12 to under 16 ft", "$16.25"),
            ("16 to under 26 ft", "$28.75"), ("26 to under 40 ft", "$78.25"),
            ("40 to under 65 ft", "$127.75"), ("65 to under 110 ft", "$152.75"),
            ("110 ft and over", "$189.75")],
   "agency": "the Florida Department of Highway Safety and Motor Vehicles, through your county tax collector",
   "agency_url": "https://www.flhsmv.gov/motor-vehicles-tags-titles/vessels/vessel-titling-registrations/",
   "src": "https://www.flhsmv.gov/pdf/proc/fees/fees-04.pdf",
   "src_name": "FLHSMV Vessel Registration Fee Chart",
   "extra": "Florida adds a service fee and may add an optional county fee on "
            "top of the base figure. Two FLHSMV pages list the add-ons "
            "differently, so treat the base fee as the reliable number and "
            "expect a few dollars more at the counter.",
   "gotcha": "Florida registers by vessel class, and the jump from Class 1 to "
             "Class 2 at 26 feet is the big one - a 25-foot boat and a 27-foot "
             "boat are nearly fifty dollars apart.",
 },
 "texas": {
   "fee_summary": '$32 under 16 feet, $53 from 16 to 26 feet, and up to $150 for 40 feet and over',
   "period": "two years",
   "rows": [("Under 16 ft (Class A)", "$32"), ("16 to under 26 ft (Class 1)", "$53"),
            ("26 to under 40 ft (Class 2)", "$110"), ("40 ft and over (Class 3)", "$150")],
   "agency": "Texas Parks & Wildlife Department",
   "agency_url": "https://tpwd.texas.gov/regulations/outdoor-annual/boating/boating-references-tools-forms",
   "src": "https://tpwd.texas.gov/regulations/outdoor-annual/boating/fees",
   "src_name": "TPWD Fee Chart for Boats and Outboard Motors",
   "extra": "Boats bought in Texas also owe 6.25% boat and motor sales tax. "
            "That is a tax, not a registration fee, and it is paid once.",
   "gotcha": "Vessels over 115 feet are not TPWD-registered at all.",
 },
 "california": {
   "fee_summary": 'a flat $20 to renew, or $29 to $49 to register for the first time depending on the year the boat was sold',
   "period": "two years, expiring 31 December of odd-numbered years",
   "rows": [("Biennial renewal", "$20"),
            ("Original registration, vessel sold in an even year", "$29"),
            ("Original registration, vessel sold in an odd year", "$49")],
   "agency": "California DMV",
   "agency_url": "https://www.dmv.ca.gov/portal/vehicle-registration/new-registration/register-your-boat-vessel/",
   "src": "https://www.dmv.ca.gov/portal/vehicle-registration/registration-fees/",
   "src_name": "California DMV Registration Fees",
   "extra": "Freshwater boats also need an Invasive Mussel Infestation "
            "Prevention sticker, which DMV collects separately from the "
            "registration fee and does not price on its fee page. Vessels "
            "used only in marine waters are exempt.",
   "gotcha": "California is one of the few states that does not charge by "
             "length - a 14-foot aluminium and a 40-foot cruiser pay the same "
             "renewal. Renewal is due by 31 December of every odd year "
             "whether the boat moved that season or not.",
 },
 "new-york": {
   "fee_summary": '$22.50 under 16 feet, $45 from 16 to 26 feet, and $75 at 26 feet and over',
   "period": "three years",
   "rows": [("Under 16 ft", "$22.50"), ("16 to under 26 ft", "$45.00"),
            ("26 ft and over", "$75.00")],
   "agency": "New York DMV",
   "agency_url": "https://dmv.ny.gov/registration/register-a-boat",
   "src": "https://dmv.ny.gov/forms/rv1.pdf",
   "src_name": "NY DMV form RV-1",
   "extra": "A $50 title fee applies to boats of model year 1987 or newer "
            "that are at least 14 feet long.",
   "gotcha": "Every motorboat operator in New York now needs a boating safety "
             "certificate, regardless of age - that phase-in completed in 2025.",
 },
 "michigan": {
   "fee_summary": '$42 for a 16-to-21-foot boat, rising to $448 at 50 feet - but a flat $23 for any pontoon',
   "period": "three years, expiring 31 March of the third year",
   "rows": [("Under 12 ft", "$14"), ("12 to under 16 ft", "$17"),
            ("16 to under 21 ft", "$42"), ("21 to under 28 ft", "$115"),
            ("28 to under 35 ft", "$168"), ("35 to under 42 ft", "$244"),
            ("42 to under 50 ft", "$280"), ("50 ft and over", "$448"),
            ("Pontoon boat, any length", "$23")],
   "agency": "Michigan Secretary of State",
   "agency_url": "https://www.michigan.gov/sos/vehicle/recreational-vehicles-watercraft",
   "src": "https://www.michigan.gov/sos/vehicle/recreational-vehicles-watercraft",
   "src_name": "Michigan SOS fee chart",
   "extra": "Non-motorised sailboats are $9. A new three-year cycle starts "
            "every 1 January and all registrations expire 31 March.",
   "gotcha": "Pontoons are the exception to Michigan's whole length-based "
             "table: $23 flat at any length. A 24-foot pontoon pays $23 where "
             "a 24-foot runabout pays $115.",
 },
 "minnesota": {
   "fee_summary": '$36 under 17 feet and $113 from 19 to 26 feet, before the invasive species surcharge',
   "period": "three years, expiring 31 December of the last year",
   "rows": [("Canoe, kayak, sailboat to 19 ft", "$23"),
            ("Pleasure craft under 17 ft", "$36"),
            ("17 to 19 ft", "$59"), ("Over 19 to under 26 ft", "$113"),
            ("26 to under 40 ft", "$164"), ("40 ft and over", "$209")],
   "agency": "Minnesota DNR",
   "agency_url": "https://www.dnr.state.mn.us/licenses/watercraft/index.html",
   "src": "https://files.dnr.state.mn.us/rlp/regulations/boatwater/boatingguide.pdf",
   "src_name": "Minnesota Boating Guide 2026, fees effective 1 January 2026",
   "extra": "Every Minnesota registration also carries an aquatic invasive "
            "species surcharge, plus a small filing fee. The surcharge rose "
            "in 2025, so the DNR's own web page and its 2026 guide disagree - "
            "the figures above are the base fees from the 2026 guide.",
   "gotcha": "The base fee is not the bill. A 17-to-19-foot boat's base fee "
             "is $59 and the guide's worked total is $96.50 once the "
             "surcharge and filing fee are added.",
 },
 "north-carolina": {
   "period": "one year or three years, owner's choice",
   "rows": [],
   "fee": False,
   "agency": "North Carolina Wildlife Resources Commission",
   "agency_url": "https://www.ncwildlife.gov/boating/registration-and-titling",
   "src": "https://www.ncwildlife.gov/boating/registration-and-titling",
   "src_name": "NC Wildlife Resources Commission",
   # The honest version. NCWRC's registration page carries no fee schedule a
   # reader can see, and the amounts on the VL-1 PDF do not extract reliably.
   # Publishing a number we inferred from garbled text would be exactly the
   # mistake this file exists to avoid.
   "fee_note": "North Carolina does not publish its vessel registration fees "
               "on the Wildlife Resources Commission's registration page, and "
               "we will not print a figure we cannot source from the state. "
               "The current amount is shown at checkout on Go Outdoors North "
               "Carolina, the state's own portal.",
   "extra": "Any vessel 14 feet or longer, and every personal watercraft, "
            "must be titled as well as registered.",
   "gotcha": "An electric trolling motor counts as mechanical propulsion in "
             "North Carolina, so a jon boat with nothing but a trolling motor "
             "still needs numbers.",
 },
 "south-carolina": {
   "fee_summary": '$10 a year, collected on your county property tax bill',
   "period": "one year, expiring in the month your county property tax is due",
   "rows": [("Annual renewal", "$10")],
   "agency": "South Carolina DNR",
   "agency_url": "https://www.dnr.sc.gov/boating/Titling_and_Registration/Fees.html",
   "src": "https://www.dnr.sc.gov/boating/Titling_and_Registration/Fees.html",
   "src_name": "SCDNR titling and registration fees",
   "extra": "Since 2020 the renewal fee is collected on your county property "
            "tax bill rather than separately by SCDNR.",
   "gotcha": "South Carolina moved from $30 every three years to $10 every "
             "year - the same money, a different rhythm - and the renewal "
             "arrives with the county tax bill, which is why people miss it.",
 },
 "georgia": {
   "fee_summary": '$35 under 16 feet, $70 from 16 to 26 feet, and up to $210 at 40 feet and over',
   "period": "three years, expiring on the last day of the owner's birth month",
   "rows": [("Under 16 ft (Class A)", "$35"), ("16 to under 26 ft (Class I)", "$70"),
            ("26 to under 40 ft (Class II)", "$140"),
            ("40 ft and over (Class III)", "$210")],
   "agency": "Georgia DNR",
   "agency_url": "https://gadnr.org/boating/registration",
   "src": "https://gadnr.org/sites/default/files/wrd/pdf/boat-registration/Vessel%20Registration%20Application.pdf",
   "src_name": "Georgia DNR Vessel Registration Application",
   "extra": "Online registration carries a $10 transaction fee, and a lapsed "
            "registration adds a $10 late fee.",
   "gotcha": "Georgia expires registrations on the owner's BIRTH MONTH, not a "
             "fixed date - so no two boats on the same dock come due together.",
 },
 "ohio": {
   "fee_summary": '$33 under 16 feet, $48 from 16 to 26 feet, and up to $93 at 65 feet and over',
   "period": "three years, expiring 1 March",
   "rows": [("Under 16 ft", "$33"), ("16 to under 26 ft", "$48"),
            ("26 to under 40 ft", "$63"), ("40 to under 65 ft", "$78"),
            ("65 ft and over", "$93"),
            ("Canoe, kayak or rowboat, any length", "$20")],
   "agency": "Ohio DNR, Division of Parks & Watercraft",
   "agency_url": "https://ohiodnr.gov/rules-and-regulations/rules-and-regulations-by-division/state-parks-and-watercraft/boating-rules/01-register-ohio-boat",
   "src": "https://ohiodnr.gov/rules-and-regulations/rules-and-regulations-by-division/state-parks-and-watercraft/boating-rules/01-register-ohio-boat",
   "src_name": "Ohio DNR, Registering Your Boat in Ohio",
   "extra": "Sail-powered boats pay $5 more in each length band.",
   "gotcha": "Ohio charges no late fee for renewing after 1 March - unusual, "
             "but the boat is still unregistered until you do.",
 },
 "iowa": {
   "fee_summary": "$28.15 to renew a 16-foot boat and $41.65 for 16 to 26 feet, through your county recorder",
   "period": "three years, the current cycle expiring 30 April 2028",
   "rows": [("No motor or sail, renewal", "$17.65"),
            ("Under 16 ft, renewal", "$28.15"),
            ("16 to under 26 ft, renewal", "$41.65"),
            ("26 to under 40 ft, renewal", "$80.65"),
            ("40 ft and over, renewal", "$155.65"),
            ("Personal watercraft, renewal", "$50.65")],
   "agency": "your county recorder, on behalf of the Iowa DNR",
   "agency_url": "https://www.iowadnr.gov/things-do/boating/boating-registration",
   "src": "https://www.iowadnr.gov/media/7419/download?inline=",
   "src_name": "Iowa DNR boat registration fee sheet",
   "extra": "A boat 17 feet or longer also needs a title, which adds $13.50. "
            "Late renewals add a $5 penalty, and mailing the renewal to the "
            "recorder adds $2.",
   "gotcha": "Iowa prices a NEW registration lower than a renewal, and the "
             "new-registration price steps down as the three-year cycle runs "
             "- so what you pay depends on when in the cycle you buy the boat.",
 },
 "wisconsin": {
   "fee_summary": "$22 under 16 feet, $32 from 16 to 26 feet, and up to $100 at 40 feet and over",
   "period": "three years, running 1 April to 31 March",
   "rows": [("Motorised, under 16 ft", "$22"), ("16 to under 26 ft", "$32"),
            ("26 to under 40 ft", "$60"), ("40 ft and over", "$100"),
            ("Non-motorised sailboat", "$17")],
   "agency": "Wisconsin DNR",
   "agency_url": "https://dnr.wisconsin.gov/permits/registrations/boat/GenInfo.html",
   "src": "https://dnr.wisconsin.gov/permits/registrations/boat/RegistrationFees.html",
   "src_name": "Wisconsin DNR boat registration fees",
   "extra": "Form 9400-193 carries the complete fee list, including the "
            "transactions this table does not cover.",
   "gotcha": "Wisconsin's registration year starts on 1 April, not 1 January "
             "- a boat registered in March gets a very short first year.",
 },
 "illinois": {
   "fee_summary": "$28 under 16 feet and $60 from 16 to 26 feet to register, with renewals lower",
   "period": "three years, expiring 30 September",
   "rows": [("Powered, under 16 ft", "$28"), ("16 to under 26 ft", "$60"),
            ("26 to under 40 ft", "$160"), ("40 ft and over", "$210")],
   "agency": "Illinois DNR",
   "agency_url": "https://dnr.illinois.gov/boating/registering.html",
   "src": "https://dnr.illinois.gov/boating/transactionfees.html",
   "src_name": "Illinois DNR transaction fees",
   "extra": "These are the new-registration and transfer figures from the "
            "DNR's own transaction page. Renewals are lower, and the DNR adds "
            "a $2 processing fee to every watercraft transaction.",
   "gotcha": "A vessel over 21 feet has to be TITLED in Illinois as well as "
             "registered - a separate transaction people miss.",
 },
 "alabama": {
   "rows": [],
   "fee": False,
   "period": "one year",
   "agency": "ALEA Marine Patrol Division, through your county licensing office",
   "agency_url": "https://www.alea.gov/dps/marine-patrol",
   "src": "https://www.alea.gov/dps/marine-patrol",
   "src_name": "ALEA Marine Patrol",
   "fee_note": "Two versions of ALEA's own registration form carry different "
               "fee tables, and neither reads cleanly enough for us to be "
               "certain which one governs. We will not print a figure on that "
               "footing. Your county licensing office has the current "
               "schedule, and ALEA's vessel registration unit will confirm it.",
   "extra": "Alabama registers through county licensing offices rather than "
            "centrally.",
   "gotcha": "Alabama is one of the states where the registration lives with "
             "the COUNTY, so two boats on the same lake can be renewed at "
             "different offices with different queues.",
 },
 "pennsylvania": {
   "fee_summary": "$26 for a motorboat under 16 feet, $39 from 16 to 20 feet, and $52 at 20 feet and over",
   "period": "two years, expiring 31 March of the second year",
   "rows": [("Unpowered boat", "$22"), ("Motorboat under 16 ft", "$26"),
            ("16 to under 20 ft", "$39"), ("20 ft and over", "$52")],
   "agency": "Pennsylvania Fish and Boat Commission",
   "agency_url": "https://www.pa.gov/agencies/fishandboat/boating/register-title-a-boat",
   "src": "https://www.pa.gov/agencies/fishandboat/faqs/boat-registration-&-titling-faqs",
   "src_name": "PFBC boat registration and titling FAQs",
   "extra": "Issuing agents add their own small agent and transaction fees on "
            "top of these.",
   "gotcha": "Pennsylvania registers UNPOWERED boats too - a kayak or canoe "
             "needs either a $22 registration or a launch permit, which is "
             "the same price.",
 },
 "louisiana": {
   "fee_summary": "$36 up to 15 ft 11 in, $57 from 16 to 25 ft 11 in, and up to $99 at 40 feet and over",
   "period": "three years from the date it is issued",
   "rows": [("Up to 15 ft 11 in", "$36"), ("16 to 25 ft 11 in", "$57"),
            ("26 to 39 ft 11 in", "$78"), ("40 ft and over", "$99")],
   "agency": "Louisiana Department of Wildlife and Fisheries",
   "agency_url": "https://www.wlf.louisiana.gov/page/title-or-register-your-boat",
   "src": "https://www.wlf.louisiana.gov/page/title-or-register-your-boat",
   "src_name": "LDWF boat title and registration",
   "extra": "Renewal costs the same as registration, and has to be done "
            "within 60 days of expiry.",
   "gotcha": "Louisiana's bands break at 15 ft 11 in and 25 ft 11 in rather "
             "than on the round foot - measure before you assume which band "
             "a 16-foot boat is in.",
 },
 "missouri": {
   "fee_summary": "$25 under 16 feet, $55 from 16 to 26 feet, and up to $150 at 40 feet and over, plus a $9 processing fee",
   "period": "three years",
   "rows": [("Under 16 ft", "$25"), ("16 to under 26 ft", "$55"),
            ("26 to under 40 ft", "$100"), ("40 ft and over", "$150")],
   "agency": "Missouri Department of Revenue",
   "agency_url": "https://dor.mo.gov/motor-vehicle/watercraft/",
   "src": "https://dor.mo.gov/motor-vehicle/titling-registration/fees.html",
   "src_name": "Missouri DOR motor vehicle fees",
   "extra": "Every transaction adds a $9 processing fee on top of the figure "
            "above.",
   "gotcha": "It is the Department of REVENUE that registers a boat in "
             "Missouri, not the Highway Patrol - the Patrol enforces boating "
             "law but does not issue the number.",
 },
 "virginia": {
   "fee_summary": "$37 under 16 feet, $41 from 16 to 20 feet, $47 from 20 to 40 feet and $55 at 40 feet and over",
   "period": "three years",
   "rows": [("Under 16 ft", "$37"), ("16 to under 20 ft", "$41"),
            ("20 to under 40 ft", "$47"), ("40 ft and over", "$55")],
   "agency": "Virginia Department of Wildlife Resources",
   "agency_url": "https://dwr.virginia.gov/boating/registration/",
   "src": "https://dwr.virginia.gov/boating/registration/procedure/",
   "src_name": "Virginia DWR, Registering and Titling Your Watercraft",
   "extra": "Virginia raised boat registration fees by $5 on 1 October 2026. "
            "The figures above are the post-increase ones; anything you find "
            "showing $32 to $50 is the old schedule.",
   "gotcha": "Virginia's bands are unusually flat - the difference between a "
             "15-foot jon boat and a 45-foot cruiser is eighteen dollars.",
 },
 "tennessee": {
   "fee_summary": "$18 a year for 16 feet and under and $35 from 16 to 26 feet, with two- and three-year options",
   "period": "one, two or three years, owner's choice",
   "rows": [("16 ft and under, one year", "$18"),
            ("16 to under 26 ft, one year", "$35"),
            ("26 to under 40 ft, one year", "$54"),
            ("40 ft and over, one year", "$72")],
   "agency": "Tennessee Wildlife Resources Agency",
   "agency_url": "https://www.tn.gov/twra/boating.html",
   "src": "https://tn.gov/twra/boating/tennessee-boating-handbook.html",
   "src_name": "TWRA Tennessee Boating Handbook, 2025 edition",
   "extra": "Two-year and three-year registrations cost proportionally more "
            "rather than less - the longest term for the longest boats runs "
            "to $203.",
   "gotcha": "Tennessee is one of the few states that lets you choose the "
             "term, so the renewal date is whatever you picked last time.",
 },
 "indiana": {
   "rows": [],
   "fee": False,
   "period": "one year",
   "agency": "Indiana BMV",
   "agency_url": "https://www.in.gov/bmv/registration-plates/boat-registration",
   "src": "https://www.in.gov/bmv/fees-taxes/boat-fees-and-taxes",
   "src_name": "Indiana BMV watercraft fees and taxes",
   "fee_note": "Indiana does not price boat registration by length alone, so "
               "there is no table to print. The bill is a length-based fee "
               "plus an annual boat excise tax set by the boat's EXCISE "
               "CLASS, which comes from its original retail price and its "
               "age. Renewal runs from about $15 for the lowest classes to "
               "$60 for the highest. The BMV's own fees page is the only "
               "honest place to work out yours.",
   "extra": "A boat kept in storage rather than used pays a flat $12 excise "
            "tax, with a storage contract as proof.",
   "gotcha": "Because Indiana charges on original retail price, a twenty-year "
             "old boat that cost a lot when new can still sit in a high "
             "excise class.",
 },
 "washington": {
   "rows": [],
   "fee": False,
   "period": "one year, every decal expiring 30 June",
   "agency": "Washington Department of Licensing",
   "agency_url": "https://dol.wa.gov/vehicles-and-boats/boats/register-boat",
   "src": "https://dol.wa.gov/vehicles-and-boats/boats/register-boat",
   "src_name": "Washington DOL, Register a boat",
   "fee_note": "Washington's $10.50 annual registration fee is only part of "
               "the bill - there are service and filing charges on top, and "
               "DOL itself tells boaters to use its fee calculator rather "
               "than quoting a total. We would rather send you to the "
               "calculator than print a number that is wrong for your boat.",
   "extra": "Vessel excise tax is a separate, one-time cost tied to the "
            "purchase, not part of the annual registration.",
   "gotcha": "Every Washington decal expires on 30 JUNE regardless of when "
             "you registered, so a boat bought in May gets about six weeks "
             "before its first renewal.",
 },
 "mississippi": {
   "fee_summary": '$25.99 for the common 16-to-26-foot band, from $10.99 for a small boat to $48.49 at the top',
   "period": "three consecutive years, beginning the day the boat is registered",
   "rows": [("Less than 16 ft", "$10.99"), ("16 ft to less than 26 ft", "$25.99"),
            ("26 ft to less than 40 ft", "$48.49"), ("40 ft and over", "$48.49")],
   "agency": "the Mississippi Department of Wildlife, Fisheries and Parks",
   "agency_url": "https://www.mdwfp.com/fishing-boating/boat-registration-renewal",
   "src": "https://www.mdwfp.com/fishing-boating/boat-registration-renewal",
   "src_name": "MDWFP Boat Registration & Renewal",
   "extra": "A dealer number is $40.99 and a duplicate registration $8.49.",
   "gotcha": "Mississippi's top two bands are the same money: a 40-footer pays the "
             "same $48.49 as a 26-footer, so there is no fee reason to round a "
             "length down once you are past 26 feet.",
 },
 "maine": {
   "fee_summary": 'by HORSEPOWER rather than length, $40 to $59 inland and $15 to $34 for tidal-only use',
   "period": "one year",
   "rows": [("10 hp or less", "$40"), ("11 to 50 hp", "$45"),
            ("51 to 115 hp", "$51"), ("Over 115 hp, and PWC", "$59")],
   "agency": "the Maine Department of Inland Fisheries and Wildlife",
   "agency_url": "https://www.maine.gov/ifw/fishing-boating/boating/index.html",
   "src": "https://legislature.maine.gov/statutes/12/title12sec13056.pdf",
   "src_name": "Maine Revised Statutes Title 12 §13056",
   "extra": "Those are the inland-water figures. A boat operated only on tidal "
            "waters pays less at every step &mdash; $15, $20, $26 and $34 "
            "respectively. A duplicate certificate or a duplicate sticker set is "
            "$1 each, and a transfer is $2. The statute schedules another rise on "
            "1 January 2028.",
   "gotcha": "Maine is the state on this list that prices the registration off the "
             "ENGINE, not the boat. A 14-foot skiff with a 150 on the back pays "
             "more than a 24-footer with a 40. And the validation stickers are "
             "nontransferable, so they do not move with a sold boat.",
 },
 "arkansas": {
   "fee_summary": '$15 for the common 16-to-26-foot band, from $7.50 for a small boat to $105 for a 40-footer',
   "period": "three years",
   "rows": [("Less than 16 ft", "$7.50"), ("16 ft to less than 26 ft", "$15.00"),
            ("26 ft to less than 40 ft", "$51.00"), ("40 ft and over", "$105.00")],
   "agency": "the Arkansas Department of Finance and Administration",
   "agency_url": "https://www.dfa.arkansas.gov/office/motor-vehicle/motor-boat-registration/",
   "src": "https://www.dfa.arkansas.gov/office/motor-vehicle/motor-boat-registration/",
   "src_name": "Arkansas DFA, Motor Boat Registration",
   "extra": "A replacement registration is $1.00.",
   "gotcha": "Arkansas registers the boat through the DEPARTMENT OF FINANCE AND "
             "ADMINISTRATION, not Game and Fish &mdash; the same office that does "
             "car tags. Game and Fish writes the boating handbook and enforces on "
             "the water, but it is not who you pay.",
 },
 "massachusetts": {
   "fee_summary": '$66 for the common 16-to-26-foot band, from $44 for a small boat to $110 for a 40-footer - and all of it buys TWO years',
   "period": "two years",
   "rows": [("Under 16 ft", "$44"), ("16 ft to less than 26 ft", "$66"),
            ("26 ft to less than 40 ft", "$88"), ("40 ft and over", "$110")],
   "agency": "the Massachusetts Environmental Police",
   "agency_url": "https://www.mass.gov/boat-registration",
   "src": "https://www.mass.gov/how-to/first-time-boat-registration",
   "src_name": "Massachusetts Environmental Police, First-time boat registration",
   "extra": "A boat title is $27.50 once, a duplicate title $16.50, and adding a "
            "lien holder $16.50.",
   "gotcha": "Massachusetts is the only state here on a TWO-year cycle &mdash; "
             "everywhere else is one year or three. Comparing its $66 against "
             "another state's annual figure makes it look twice as expensive as it "
             "is.",
 },
 "new-jersey": {
   "fee_summary": '$28 a year for the common 16-to-26-foot band, from $12 for a small boat to $250 for anything 65 feet and over',
   "period": "one year",
   "rows": [("Less than 16 ft", "$12.00"), ("16 ft to less than 26 ft", "$28.00"),
            ("26 ft to less than 40 ft", "$52.00"),
            ("40 ft to less than 65 ft", "$80.00"), ("65 ft or more", "$250.00")],
   "agency": "the New Jersey Motor Vehicle Commission",
   "agency_url": "https://www.nj.gov/mvc/vehicles/boating.htm",
   "src": "https://www.nj.gov/mvc/vehicles/regfees.htm",
   "src_name": "NJ MVC registration fees",
   "extra": "Those are the non-commercial figures. A commercial vessel pays $1 more "
            "in every band. The statute, N.J.S.A. 12:7-34.47, states each of them "
            "&ldquo;per year&rdquo;, which is where the one-year term comes from.",
   "gotcha": "New Jersey's top band is the steepest jump on this page: $80 at 64 "
             "feet becomes $250 at 65. It is also one of the few states where the "
             "SELLER is required to remove the decals when the boat changes hands.",
 },
}


def fee_rows(slug):
    """Published bands for a state, or [] when the state publishes none."""
    f = FEES.get(slug)
    return (f or {}).get("rows") or []


def has_fee(slug):
    f = FEES.get(slug)
    return bool(f) and f.get("fee", True) and bool(f.get("rows"))
