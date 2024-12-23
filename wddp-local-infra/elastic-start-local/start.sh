#!/bin/sh
# Start script for start-local
# More information: https://github.com/elastic/start-local
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd ${SCRIPT_DIR}
today=$(date +%s)
. ./.env
if [ ! -n "${ES_LOCAL_LICENSE:-}" ] && [ "$today" -gt 1732740488 ]; then
  echo "---------------------------------------------------------------------"
  echo "The one-month trial period has expired. You can continue using the"
  echo "Free and open Basic license or request to extend the trial for"
  echo "another 30 days using this form:"
  echo "https://www.elastic.co/trialextension"
  echo "---------------------------------------------------------------------"
  echo "For more info about the license: https://www.elastic.co/subscriptions"
  echo
  echo "Updating the license..."
  docker compose up --wait elasticsearch >/dev/null 2>&1
  result=$(curl -s -X POST "${ES_LOCAL_URL}/_license/start_basic?acknowledge=true" -H "Authorization: ApiKey ${ES_LOCAL_API_KEY}" -o /dev/null -w '%{http_code}\n')
  if [ "$result" = "200" ]; then
    echo "✅ Basic license successfully installed"
    echo "ES_LOCAL_LICENSE=basic" >> .env
  else 
    echo "Error: I cannot update the license"
    result=$(curl -s -X GET "${ES_LOCAL_URL}" -H "Authorization: ApiKey ${ES_LOCAL_API_KEY}" -o /dev/null -w '%{http_code}\n')
    if [ "$result" != "200" ]; then
      echo "Elasticsearch is not running."
    fi
    exit 1
  fi
  echo
fi
docker compose up --wait
