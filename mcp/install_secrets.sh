#!/usr/bin/env bash
# Install the case-study pipeline's secrets on the Worker.
#
# RUN THIS YOURSELF. Every value is piped from a file you control, so nothing
# is typed at a prompt, nothing lands in shell history, and no key is ever
# pasted into a chat transcript.
#
#   ~/.dataforseo.env          DATAFORSEO_LOGIN= / DATAFORSEO_PASSWORD=
#   ~/.nmb-gsc-sa.json         the Google service-account JSON, whole file
#   ~/.nmb-ga4-property        the GA4 numeric property id, one line
#   ~/.nmb-bing-key            the Bing Webmaster API key, one line
#
# Anything missing is skipped and reported - the pipeline is per-source, so a
# missing Bing key costs you Bing and nothing else.
set -u
cd "$(dirname "$0")/.." || exit 1

export CLOUDFLARE_ACCOUNT_ID=681da9da7939c8989b00fb80ee4a791c
export NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem
W="npx wrangler secret put"

put_file() {  # name, path
  if [ -s "$2" ]; then
    printf '%s' "$(cat "$2")" | $W "$1" && echo "  set $1" || echo "  FAILED $1"
  else
    echo "  skipped $1 (no $2)"
  fi
}

echo "DataForSEO"
if [ -s ~/.dataforseo.env ]; then
  for k in DATAFORSEO_LOGIN DATAFORSEO_PASSWORD; do
    v=$(grep "^$k=" ~/.dataforseo.env | head -1 | cut -d= -f2-)
    if [ -n "$v" ]; then
      printf '%s' "$v" | $W "$k" >/dev/null && echo "  set $k" || echo "  FAILED $k"
    else
      echo "  skipped $k (not in ~/.dataforseo.env)"
    fi
  done
else
  echo "  skipped (no ~/.dataforseo.env)"
fi

echo "Google Search Console + GA4"
put_file GSC_SERVICE_ACCOUNT_JSON ~/.nmb-gsc-sa.json
put_file GA4_PROPERTY_ID          ~/.nmb-ga4-property
# The property form matters: a Domain property in Search Console is
# "sc-domain:numbermyboat.com", a URL-prefix property is the URL with the
# trailing slash. Getting it wrong returns 403, which reads like a bad key.
printf '%s' "sc-domain:numbermyboat.com" | $W GSC_SITE_URL >/dev/null \
  && echo "  set GSC_SITE_URL (sc-domain:numbermyboat.com)"

echo "Bing"
put_file BING_API_KEY ~/.nmb-bing-key

echo
echo "Then force one pull and look at what came back:"
echo "  curl -s -X POST \"https://numbermyboat.com/api/cron/case-study-refresh?k=\$(cat ~/.numbermyboat-runkey)&force=1\" | python3 -m json.tool"
echo
echo "The service account needs to be an OWNER on the Search Console property."
echo "Full is not enough for the API and it fails as a 403 that reads like a"
echo "bad key. In GA4 it needs Viewer on the property."
