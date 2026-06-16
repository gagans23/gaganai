#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${PARALLEL_API_KEY:-}" ]]; then
  echo "PARALLEL_API_KEY is not set."
  echo "Run: export PARALLEL_API_KEY=\"your_parallel_key\""
  exit 1
fi

curl -sS https://api.parallel.ai/v1beta/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${PARALLEL_API_KEY}" \
  -d '{
    "objective": "Find the most important AI, agentic AI, cloud, banking, fintech, central bank, data center, and enterprise technology news in the GCC region from the last 24 to 72 hours. Prefer primary sources, regulators, company announcements, and credible business press. Return sources useful for a LinkedIn executive newsletter.",
    "search_queries": [
      "GCC AI news today banks fintech cloud central bank",
      "UAE Saudi Qatar Bahrain Kuwait Oman artificial intelligence news today",
      "GCC agentic AI cloud providers banking fintech announcement",
      "Middle East AI regulation central bank fintech cloud data center news"
    ],
    "mode": "fast",
    "max_results": 10,
    "excerpts": {
      "max_chars_per_result": 3000
    }
  }' | jq '.'
