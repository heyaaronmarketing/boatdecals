# -*- coding: utf-8 -*-
"""The "share this in your group" block.

Written for how boating groups actually work, not how a share button wishes
they did:

  * Most groups ban links in the post body, so every pre-written post ends
    "link in comments" and the copied text carries the URL separately.
  * Admins remove undisclosed promotion, so every post discloses. That is not
    politeness, it is what keeps the account from being banned.
  * The UTM tag goes on the COPIED text only - never on og:url or the
    canonical, which must stay clean.

No tracking scripts, no third-party embeds. One clipboard call.
"""

UTM = "?utm_source=facebook&utm_medium=group&utm_campaign=share"


def posts_for(path, state=None):
    """Two or three posts, each under 300 characters.

    Every one of them discloses the family connection and every one says
    "link in comments" - verify.py fails the build otherwise. Those are not
    style preferences: an undisclosed promo post gets the poster banned, and
    most boating groups delete links in the body.
    """
    if state:
        return [
          ("Compliance",
           "PSA before the season: %s bow numbers start with %s, and they have "
           "to be 3\u2033 plain block with a letter-width space between the "
           "groups (%s 1234 AB, not %s1234AB). Italics and run-together "
           "numbers are what gets warnings. Free checker \u2014 link in "
           "comments. Full disclosure, it's my brother's site."
           % (state["name"], state["ab"], state["ab"], state["ab"])),
          ("Price",
           "Need %s registration numbers? $19 a pair, both sides, 3\u2033 "
           "legal block vinyl pre-spaced on one sheet so you're not lining up "
           "twelve loose letters. Free shipping, and they email a proof first. My "
           "brother cuts them in Iowa \u2014 link in comments \U0001f6a4"
           % state["name"]),
        ]
    return [
      ("Compliance",
       "Quick PSA: your bow numbers have to be 3\u2033 plain block characters "
       "with a letter-width space between the groups (IA 1234 AB, not "
       "IA1234AB). Italics and no spacing are the #1 warning I hear about. "
       "Free 30-second checker \u2014 link in comments. Full disclosure, my "
       "brother runs it. \u2705"),
      ("Price",
       "Registration numbers: $19 a pair, both sides, 3\u2033 legal block "
       "vinyl pre-spaced on one sheet so you're not lining up twelve loose "
       "letters. Free shipping, and a proof to approve first. "
       "It's my brother's shop in Iowa \u2014 link in comments \U0001f6a4"),
      ("New owner",
       "Just bought a boat? The checklist nobody gives you: register it, put "
       "3\u2033 block numbers on BOTH sides of the forward half in a "
       "contrasting color, and the state decal goes next to them. Happy to "
       "answer questions \u2014 my family cuts numbers if you need a pair, "
       "link in comments."),
    ]


def block(path, url, img, state=None):
    items = []
    for i, (label, text) in enumerate(posts_for(path, state)):
        items.append(
          '<div class=sbpost>'
          '<div class=sbhead><b>%s</b>'
          '<button type=button class=sbcopy data-i="%d">Copy post</button></div>'
          '<p class=sbtext id="sbt%d">%s</p></div>' % (label, i, i, text))
    share = ("https://www.facebook.com/sharer/sharer.php?u="
             + (url + UTM).replace(":", "%3A").replace("/", "%2F")
                          .replace("?", "%3F").replace("&", "%26")
                          .replace("=", "%3D"))
    return (
      '<section class=soft id=share><div class=w>'
      '<h2>Share this in your boating group</h2>'
      '<p class=lede>Groups delete link posts and keep photo posts. Download '
      'the picture, post it natively, and put the link in the first comment '
      '&mdash; and say it is a family business, because admins check.</p>'
      '<div class=sbgrid><div class=sbposts>%s</div>'
      '<div class=sbside>'
      '<img class=sbimg src="%s" alt="Share card for this page" '
      'width="1200" height="630" loading="lazy">'
      '<a class="btn sbdl" href="%s" download>Download the image</a>'
      '<a class=sblink href="%s" rel="nofollow noopener" target="_blank">'
      'Share to Facebook &rarr;</a>'
      '<p class=sbnote>The copied text includes the link with a tracking tag, '
      'so you can tell which group it came from.</p>'
      '</div></div>'
      '<div class=sbtoast id=sbtoast role=status aria-live=polite></div>'
      '</div></section>'
      '<script>(function(){var u=%s;'
      'document.querySelectorAll(".sbcopy").forEach(function(b){'
      'b.addEventListener("click",function(){'
      'var t=document.getElementById("sbt"+b.dataset.i).textContent.trim()+"\\n\\n"+u;'
      '(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject())'
      '.then(function(){var e=document.getElementById("sbtoast");'
      'e.textContent="Copied \\u2014 paste it, then put the link in the first comment.";'
      'e.classList.add("on");setTimeout(function(){e.classList.remove("on");},2600);})'
      '.catch(function(){var e=document.getElementById("sbtoast");'
      'e.textContent="Select the text and copy it manually.";e.classList.add("on");});'
      '});});})();</script>'
      % ("".join(items), img, img, share,
         '"' + url + UTM + '"'))
