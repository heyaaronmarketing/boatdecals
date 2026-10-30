# After deploy: Facebook share checklist

Run this once the domain is routed at the Worker. Nothing here can be done
before then — Facebook's crawler has to be able to reach numbermyboat.com,
and today it resolves to nothing.

## 1. Pre-cache the cards

Facebook does not render an image for the FIRST person who shares a URL
unless it has already scraped it. Paste each of these into
<https://developers.facebook.com/tools/debug/> and press **Scrape Again**:

- [ ] `https://numbermyboat.com/`
- [ ] `https://numbermyboat.com/design/`
- [ ] `https://numbermyboat.com/boat-registration-numbers/`
- [ ] `https://numbermyboat.com/pricing/`
- [ ] `https://numbermyboat.com/tools/registration-number-layout-checker/`
- [ ] `https://numbermyboat.com/tools/boat-name-generator/`
- [ ] the three or four state pages you plan to post first

Confirm each shows the **-v2** image and no warnings.

## 2. Eyeball the mobile crop

Paste one URL into a private post and into a Messenger chat. Messenger,
WhatsApp and iMessage crop toward the centre, so check the headline and the
price badge both survive a square crop.

## 3. Posting, in order of what actually works

1. **Photo post, not a link post.** Upload the card from
   `/assets/share/` (or a real photo of a hull) and put the link in the
   **first comment**. Meta has been testing a 2-link-post-a-month cap on
   Pages; links in comments are not affected.
2. **Use the square or portrait version** where the group's feed is
   phone-first — every card ships as `-sq` (1080×1080) and `-tall`
   (1080×1350) alongside the 1200×630.
3. **Read the pinned rules before posting.** Most boating groups allow
   links only in comments, and the usual reason a post gets pulled is
   undisclosed promotion.
4. **Ask the admin first** in buy/sell and lake groups. An approved post
   gets pinned; an unapproved one gets reported.
5. **Never paste the same text into two groups on the same day.** Vary the
   hook — there are three on the homepage block and two on every state page.

## 4. Never share the staging URL

`boatdecals.aironz.workers.dev` runs the sandbox card form. A group member
could "pay" on it and receive nothing. verify.py fails the build if a
workers.dev URL ever reaches a meta tag, but it cannot stop a human pasting
one into a group.

## 5. Measure

The copied post text carries
`?utm_source=facebook&utm_medium=group&utm_campaign=share`. The canonical and
og:url stay clean. After four to six weeks, compare groups and hooks and let
that decide where to keep posting.
