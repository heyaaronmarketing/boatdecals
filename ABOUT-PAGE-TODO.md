# About page — what's live, what's outstanding

Built from `About Ryan — Boat Decals Site.md` (Aaron, 2026-10-23).
Live at `/about/`.

## Still needs a person's say-so

The brief's own pre-publish checklist left these unticked, and the page is
live, so they are published right now. Each is one edit in `engine/content.py`
under `ABOUT`:

- [ ] **Ryan approves the fire-chief framing** and the links to the city site,
      the council agenda and the KWWL story. Worth confirming the department
      has no rule against a commercial site implying endorsement.
- [ ] **Stacy approves being named.** `ABOUT["name_stacy"] = False` removes the
      sentence and nothing else moves.
- [ ] **Ryan confirms the rental section stays.** `ABOUT["rentals"] = False`
      drops it; the "holds up to Iowa weather" idea already appears in the
      section below it, so nothing is lost.
- [ ] **Turnaround.** The brief had `[X]`. The page says "the next business
      day", matching the rest of the site. If the real answer is two days,
      change `ABOUT["turnaround"]` and the whole site stays consistent.

## Photographs — none are on the page

Every image the brief calls for is either a Facebook screenshot (the brief
says plainly: get the originals, Facebook compresses hard) or a shot that does
not exist yet.

**The site's own imagery was deliberately NOT used to fill the gaps.** Those are
AI-generated illustrative product shots of nobody's boat. Captioning one as
Ryan's bench or Ryan's hull would present a generated image as a real named
person's work. `media/CAPTIONS.md` already forbids that for customers; it
matters more for the owner, not less.

So every section is written to stand up as type, and the slots drop in without
a rewrite.

### Get the originals from Ryan
| # | Photo | Goes in | Crop |
|---|---|---|---|
| 1 | Motocross jump (orange gear, green bike, mid-air) | Hero | 16:9, rider right of centre, darken 20% behind the headline |
| 2 | Profile photo (dark FD polo, outdoors) | The day job | Square portrait. Swap for a Ryan + Stacy uniform shot if one exists |
| 3 | Rental house exterior | The landlord | 3:2 landscape, house number cropped or blurred |
| 4 | Kitchen rehab interior | The landlord inset | Square, optional |
| 5 | Harley from the 2021 rally post | Fast toys | Square, keep monochrome |
| 6 | Camo hunting photo | Fast toys | Square, head and shoulders |
| 7 | Lake / dock shot | Closing banner | Wide |

The NCC MX series flyer is left out until someone confirms the series is fine
with its logo on a commercial page.

### Still to shoot
- [ ] Ryan at the cutter, weeding a boat name, over the shoulder
- [ ] Finished registration numbers on a hull, close and angled
- [ ] Ryan on or beside his own boat with his own decals visible
- [ ] Flat-lay of a decal set, transfer tape half peeled

## Excluded on purpose
Birthdate, home and rental street addresses, the firearms and suppressor
posts, and the kids. Verified absent from the built page.

## Links
Three of the brief's five authority links are live on the page. Radio Iowa and
the Iowa Firefighters Association roster both 403 to anything that is not a
browser, and a dead authority link is worse than none, so they are out.
