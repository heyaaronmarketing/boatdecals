# -*- coding: utf-8 -*-
"""Reusable prose. The federal rule block is quoted from 33 CFR 173.27 and was
verified against the CFR text on 2026-10-22 - do not paraphrase it loosely,
this is compliance content and people buy on it."""

# The actual regulation. Four requirements, and every state adopts them.
FED_RULE = """<div class=rule>
<p><strong>The federal rule, in full.</strong> Under 33 CFR 173.27, a registration
number must:</p>
<ul>
<li>be painted on or permanently attached to <strong>each side of the forward half</strong>
of the vessel;</li>
<li>be in <strong>plain vertical block characters of not less than 3 inches in
height</strong>;</li>
<li><strong>contrast with the colour of the background</strong> and be distinctly
visible and legible;</li>
<li>have <strong>spaces or hyphens</strong> between the letter and number groupings
equal to the width of a letter other than &ldquo;I&rdquo; or a number other than
&ldquo;1&rdquo; &mdash; so <strong>TX 1234 AB</strong>, not TX1234AB;</li>
<li><strong>read from left to right.</strong></li>
</ul>
<cite>33 CFR &sect; 173.27 &mdash; Numbers: Display; size; colour. Applies in every
state. Your state can add to it, but cannot drop below it.</cite>
</div>"""

CONTRAST_NOTE = """<div class=note>
<p><b>The rule most people miss is contrast.</b> There is no required colour &mdash;
but white numbers on a white hull are not &ldquo;distinctly visible and legible,&rdquo;
and that is a failed inspection. Dark hull, light numbers. Light hull, dark numbers.
Our order form flags the combination before it gets cut.</p></div>"""

APPLY_STEPS = """<ol class=steps>
<li><strong>Wash, then wipe with alcohol.</strong> Soap leaves a film and wax is the
enemy of adhesive. Finish with isopropyl alcohol on a clean rag and let it flash off.
Skip this and nothing else you do matters.</li>
<li><strong>Check the temperature.</strong> Between 50&deg;F and 90&deg;F, out of
direct sun. Cold vinyl will not tack; a hot hull grabs before you can position it.</li>
<li><strong>Tape it in position dry.</strong> Hold the sheet where you want it and run
a strip of masking tape along the top edge as a hinge. Step back fifteen feet and look
at it before you commit &mdash; eyeballing from two feet away is how numbers end up
crooked.</li>
<li><strong>Wet the hull.</strong> A few drops of dish soap in a spray bottle of water.
Mist the hull generously. This is the wet method and it buys you the ability to slide
and reposition.</li>
<li><strong>Flip down and squeegee from the centre out.</strong> Peel the paper backing
away, lay the sheet onto the wet hull, then squeegee firmly from the middle toward each
edge. Overlap your strokes. You are pushing water and air out, not polishing.</li>
<li><strong>Wait, then pull the tape back on itself.</strong> Give it fifteen minutes.
Pull the clear application tape off at a sharp angle, flat back against itself &mdash;
not straight out. If a letter lifts, lay the tape back down, squeegee that spot again
and wait longer.</li>
<li><strong>Leave it alone for 24 hours.</strong> No pressure washing, no launching if
you can help it. The adhesive is still curing.</li>
</ol>"""

# Three cards, not six. The proof, the re-cut and the pre-spacing claims were
# cut on 2026-10-23; the warranty and shipping pages still carry those terms in
# full, they just no longer lead the product pages.
WHY_US = [
 ("$19 a pair, published",
  "Every competitor makes you build a design before showing a price. Ours is on the "
  "page and it includes shipping."),
 ("Cut and shipped next business day",
  "Cut the next business day and in the post the same afternoon, free. No queue, "
  "no proof to approve first."),
 ("Marine Vinyl",
  "Marine film built for sun, salt and spray, not the craft stock the cheap sets "
  "use. High-tack on plastic hulls at no extra charge."),
]

# Four steps, four cards. (title, body) - build.py numbers them.
# No proof step. The live preview IS the proof - it shows the actual lettering,
# in the chosen font and colour, at the chosen height, before any money moves.
# That is why the preview and the number validator earn their keep.
HOW_IT_WORKS_STEPS = [
 ("Type what it should say",
  "Straight off your registration card for numbers, or whatever you have "
  "picked for a name."),
 ("Pick height, font and colour",
  "The form only offers block faces once you choose registration numbers, "
  "because the law requires them."),
 ("Check the preview",
  "It shows your exact lettering, at your height, in your colour. We cut "
  "what is on that screen - so read it twice."),
 ("We cut it and ship it",
  "Next business day, free, pre-spaced with application tape over the top."),
]

# ---------------------------------------------------------------- guide FAQs
# Every guide used to ship the SAME two shop questions ("what does it cost",
# "do you ship to my state"). Eight FAQPage blocks answering one question is
# worth roughly one FAQPage block, and none of them answered what the page was
# actually about - which is the only thing an AI engine would want to quote.
#
# House style for these, because it is what gets lifted into an answer box:
#   * the question is phrased the way a person types it, not the way we would
#     title a section
#   * the FIRST SENTENCE is the whole answer. No preamble, no "it depends"
#   * the specifics are in it - 3 inches, 33 CFR 173.27, $19, next business day
#   * one shop question per guide at most, and only where it actually follows
GUIDE_FAQS = {
 "boat-registration-number-rules": [
  ("How big do boat registration numbers have to be?",
   "At least 3 inches tall. Federal rule 33 CFR 173.27 sets 3 inches as the minimum "
   "for the block characters on the bow, and every state adopts that floor. Nothing "
   "stops you going bigger, and a few owners do for readability."),
  ("What font is legal for boat registration numbers?",
   "Plain vertical block characters. Script, italic, outline and heavily stylised "
   "faces are not legal for the registration number, because 33 CFR 173.27 requires "
   "plain block letters that read clearly at a distance. A boat name on the transom "
   "has no such rule, so script is fine there."),
  ("Do boat registration numbers have to be a certain colour?",
   "No specific colour, but they must contrast with the hull. The rule says the "
   "characters must be of a colour that contrasts with the background so they are "
   "distinctly visible - white on a dark hull, black on a light one. White on cream "
   "is the common failure."),
  ("Do I need spaces or hyphens between the number groups?",
   "Yes - the prefix, the digits and the suffix must be separated by a space or a "
   "hyphen equal to the width of a letter. IA 3717 ZW, not IA3717ZW."),
  ("Where do the registration numbers go on a boat?",
   "On the forward half of both sides of the hull, reading left to right. The "
   "validation decal goes within six inches of the number, which side and which end "
   "depends on your state."),
  ("Are boat registration number rules the same in every state?",
   "The display rules are federal and identical in all 50 states. The number FORMAT "
   "differs: the two-letter vessel prefix is not always the postal code, and a few "
   "states allow letter patterns others do not."),
 ],
 "where-to-put-boat-registration-numbers": [
  ("Where exactly do boat registration numbers go?",
   "On the forward half of both sides of the hull, as high above the waterline as "
   "practical, reading left to right. Both sides get the same number - that is why "
   "a set is a pair."),
  ("Which side does the validation sticker go on?",
   "Within six inches of the registration number, but the exact position is a state "
   "rule rather than a federal one. Most states say aft of the number; some specify "
   "forward. Check your state page before you stick it down."),
  ("How high above the waterline should the numbers be?",
   "As high as the hull shape practically allows, on a flat run of topsides. The "
   "point is that they stay readable when the boat is loaded and under way, so avoid "
   "a spot that sits in the spray or gets covered by a rub rail."),
  ("Can registration numbers go on the windshield or a board?",
   "Not on the windshield. They must be on the hull itself. Some states allow a "
   "bracket-mounted plate for inflatables and boats with no suitable flat surface, "
   "which is the exception rather than the rule."),
  ("Do both sides of the boat need registration numbers?",
   "Yes, both sides, forward half, same number. That is the entire reason our $19 "
   "price is for a pair rather than a single set."),
 ],
 "how-to-apply-boat-lettering": [
  ("How do you apply vinyl boat lettering?",
   "Clean the hull with soap then alcohol, tape the sheet in position dry, wet the "
   "hull with soapy water, peel the backing, squeegee from the centre out, then pull "
   "the application tape back on itself. Leave it 24 hours before launching."),
  ("What temperature do you need to apply boat lettering?",
   "Above about 50 degrees F, on a surface that is not in direct hot sun. Cold "
   "adhesive will not grab and a hot hull makes the vinyl stretch and tack down "
   "before you have it straight."),
  ("Should I apply boat lettering wet or dry?",
   "Wet, for anything longer than a few characters. A few drops of dish soap in a "
   "spray bottle lets you slide the vinyl into position instead of committing on "
   "contact. Short numbers are fine dry if you have hinged them with tape."),
  ("How long before I can put the boat in the water?",
   "24 hours. The adhesive keeps curing after it looks finished, so no pressure "
   "washing and no launching for a day."),
  ("What happens if I get the lettering crooked?",
   "Tell us and we cut it again free. One re-cut per order, no photographs and no "
   "argument - a torn character, a creased sheet or a set that went on crooked all "
   "count."),
  ("Do I need special tools to apply boat lettering?",
   "A felt squeegee, a spray bottle and masking tape. A set ships with a basic "
   "squeegee; the fluid and the tape you can assemble from a kitchen and a hardware "
   "drawer."),
 ],
 "how-to-remove-boat-lettering": [
  ("How do you remove old boat lettering?",
   "Warm the vinyl with a heat gun on low or a hairdryer, lift an edge with a "
   "plastic razor, and peel slowly at a shallow angle keeping the heat just ahead of "
   "the peel. Then remove the adhesive separately with a citrus or mineral-spirit "
   "remover, and polish."),
  ("Will removing boat lettering damage the gelcoat?",
   "Not if you keep the heat moving and never use a steel blade. The damage people "
   "do is from overheating one spot until the gelcoat blisters, or from scraping "
   "with metal. Use plastic and patience."),
  ("What removes the sticky adhesive left behind by decals?",
   "A citrus-based adhesive remover or mineral spirits, left to dwell a minute "
   "before you wipe. Scrubbing dry adhesive just smears it. Repeat rather than "
   "press harder."),
  ("What is the ghost outline left after removing boat lettering?",
   "It is the unfaded gelcoat that the old vinyl was protecting. The hull around it "
   "has weathered for years while that patch has not. A machine polish and a season "
   "of sun will even it out; a compound cuts it faster."),
  ("Do I have to remove the old name before renaming a boat?",
   "Practically, yes - remove every trace first, including logbooks and life rings, "
   "then apply the new one. Superstition aside, new vinyl over a ghost outline shows "
   "the old name through it in raking light."),
 ],
 "boat-lettering-fonts": [
  ("What is the best font for boat lettering?",
   "A heavy, wide face with open counters. The practical test is distance: thin "
   "strokes and tight letter shapes disappear at fifty yards and photograph as a "
   "smudge. Pick weight over flourish for anything you want read from the next slip."),
  ("Can I use a script font for boat registration numbers?",
   "No. Registration numbers must be plain vertical block characters under 33 CFR "
   "173.27, so script, italic and outline faces are not legal. Our order form hides "
   "them the moment you pick registration numbers."),
  ("Can I use script for a boat name?",
   "Yes. A transom name has no font rule at all, so script, serif and anything else "
   "is fair game. Script is the single most popular choice for a boat name and "
   "roughly half our name orders use one."),
  ("How many fonts do you offer?",
   "Ten, each previewed in your own lettering before you order. Five are plain block "
   "faces and are the only ones offered for registration numbers; the other five are "
   "for names and lettering."),
  ("Does the font change the price?",
   "No. Price follows the finished size of the decal, not which face you pick. A "
   "script name and a block name of the same overall dimensions cost the same."),
 ],
 "best-vinyl-for-boat-lettering": [
  ("What kind of vinyl is used for boat lettering?",
   "Marine-grade cut vinyl, not printed film and not craft stock. The letter shapes "
   "are cut from a sheet of coloured vinyl so there is no clear background or visible "
   "edge on the hull - just the characters."),
  ("What is the difference between cast and calendared vinyl?",
   "Cast film is poured and cured flat so it carries no internal stress, which makes "
   "it thinner, more conformable and longer lived outdoors. Calendared film is rolled "
   "into sheet and slowly tries to shrink back, which is what lifts old decals at the "
   "corners. For a flat transom on a trailered boat, calendared is genuinely fine."),
  ("Why will not vinyl stick to my kayak or jet ski?",
   "Because rotomoulded polyethylene has a low surface energy - almost nothing "
   "sticks to it. Standard adhesive holds for a few weeks then releases in one clean "
   "piece. It needs high-tack film, which we send free on every kayak, canoe and PWC "
   "order."),
  ("Does vinyl stick to a textured pontoon rail?",
   "Only high-tack film does. Brushed and painted aluminium with any texture gives "
   "standard adhesive too little contact area. We ship high-tack for pontoon rails by "
   "default for that reason."),
  ("Can I put boat lettering over wax?",
   "No. Wax, polish and polymer sealant are exactly what the adhesive cannot grip. "
   "Wash with soap, then wipe the area with isopropyl alcohol immediately before you "
   "apply - soap leaves a film of its own."),
 ],
 "documented-vessel-name-and-hailing-port": [
  ("Does a USCG documented vessel display state registration numbers?",
   "No. A documented vessel does not carry state registration numbers on the bow. It "
   "is marked with its name and hailing port instead, and the official number is "
   "marked separately inside the hull."),
  ("How tall must the name on a documented vessel be?",
   "At least 4 inches. The name and hailing port must be in clearly legible "
   "characters not less than four inches in height, together on a clearly visible "
   "exterior part of the hull - in practice the transom."),
  ("Where does the hailing port go on a documented vessel?",
   "With the name, on a clearly visible exterior part of the hull, and it must "
   "include a place and a state. City and state, spelled out or with the standard "
   "state abbreviation."),
  ("How big must the official number inside a documented vessel be?",
   "3 inches, permanently affixed to an integral part of the hull's interior "
   "structure, in a way that alteration or removal would be obvious. It is not the "
   "same thing as the hull identification number."),
  ("Can two boats have the same name?",
   "On state-registered boats, yes - names are not registered or protected and there "
   "are hundreds of boats called Serenity. The Coast Guard will not document two "
   "vessels with the same name and the same hailing port."),
 ],
 "boat-registration-number-cost": [
  ("How much do boat registration numbers cost?",
   "$19 a pair from us, with free shipping, which covers both sides of the bow. "
   "Across the market, online sets run roughly $10 to $25 a pair; a sign shop will "
   "usually quote $9 to $15 but asks you to specify everything yourself."),
  ("Why are some boat registration numbers so much cheaper?",
   "Because they are cut as loose individual characters rather than pre-spaced on "
   "one sheet, so you do the spacing on the water and the legal spacing is your "
   "problem. Cheap sets are also usually craft-grade calendared film."),
  ("Is shipping included in the price of boat numbers?",
   "Yes, free to all 50 states and DC. A $12 set with $6 shipping is an $18 set, "
   "which is the comparison that actually matters when you are shopping around."),
  ("How much does a boat name decal cost?",
   "From $29, including shipping. Most transom names land between $29 and $79, and "
   "price follows the finished size of the decal rather than the number of letters."),
  ("How long does it take to get boat registration numbers?",
   "Cut and shipped the next business day, then 3 to 6 days in standard post. If you "
   "need it faster than that, email before you order and we will say what is "
   "possible."),
 ],
}
