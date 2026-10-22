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

WHY_US = [
 ("$19 a pair, published",
  "Every competitor makes you build a design before showing a price. Ours is on the "
  "page and it includes shipping."),
 ("Cut and shipped next business day",
  "Order before 1pm CT and it goes out the same day for $12. Otherwise next business "
  "day, free."),
 ("7-year marine vinyl",
  "Cast vinyl rated seven years outdoors, not the 3-year calendared stock the cheap "
  "sets use. High-tack on plastic hulls at no extra charge."),
 ("Pre-spaced on one sheet",
  "The spacing is already legal and already right. You apply the whole set in one "
  "pass instead of placing loose characters and hoping."),
 ("A proof before anything is cut",
  "You see exactly what you are getting, by email. Do not like it? We redraw it, or "
  "refund you in full."),
 ("Free re-cut if the install goes wrong",
  "Tear a letter, crease the sheet, change your mind on the colour mid-job &mdash; "
  "tell us and we cut it again. Vinyl is cheap; arguing is expensive."),
]

HOW_IT_WORKS = """<ol class=steps>
<li><strong>Type what it should say.</strong> Straight off your registration card for
numbers, or whatever you have picked for a name.</li>
<li><strong>Pick height, font and colour.</strong> The form locks script fonts out of
registration numbers, because the law requires block characters.</li>
<li><strong>We email you a proof.</strong> Usually within a few hours during the
working day. Nothing is cut yet, and you can still change anything &mdash; or
cancel for a full refund.</li>
<li><strong>You approve, we cut and ship.</strong> Next business day, free, pre-spaced
with application tape over the top.</li>
</ol>"""

VINYL_TABLE = [
 ("Cast (premium, 8&nbsp;yr)", "Poured as a liquid, so it has no built-in stress. "
  "Conforms to compound curves and holds colour longest.",
  "Boats that live outside, dark colours, curved transoms", "+$8"),
 ("Calendared (standard, 5-7&nbsp;yr)", "Rolled into sheet. Slightly thicker, "
  "wants to shrink back over years.",
  "Flat panels, trailered boats, most registration numbers", "included"),
 ("High-tack", "Same film, much more aggressive adhesive.",
  "Polyethylene kayaks, PWC hulls, textured pontoon rails, carpet",
  "free when you need it"),
 ("Reflective", "Glass-bead layer returns light to its source.",
  "Being seen at night, working and patrol boats", "+$10"),
]
