import os
import sys

from parallel import Parallel


def build_parallel_client():
    api_key = os.environ.get("PARALLEL_API_KEY")
    if not api_key:
        print('PARALLEL_API_KEY is not set. Run: export PARALLEL_API_KEY="your_parallel_key"', file=sys.stderr)
        return None

    base_url = os.environ.get("PARALLEL_BASE_URL")
    if not base_url:
        gateway_port = os.environ.get("OPENCLAW_GATEWAY_PORT", "").strip()
        if gateway_port:
            base_url = f"http://127.0.0.1:{gateway_port}"

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return Parallel(**kwargs)


def main():
    client = build_parallel_client()
    if client is None:
        return 1

    response = client.search(
        search_queries=[
            "last 7 days GCC central bank AI fintech regulation UAE Saudi Qatar Bahrain Kuwait Oman",
            "last 7 days GCC banks AI cloud fintech FAB Emirates NBD QNB Mashreq ADCB SNB HSBC Citi Standard Chartered",
            "last 7 days GCC cloud providers AI data center AWS Microsoft Google Oracle IBM Aramco HUMAIN UAE Saudi Qatar",
            "last 7 days GCC government artificial intelligence agentic AI announcement UAE Dubai Saudi Qatar",
            "last 7 days GCC fintech payments open banking digital assets stablecoin AI regtech",
        ],
        mode="advanced",
        advanced_settings={"max_results": 10},
        objective=(
            "Find only credible news or official announcements from the last 7 calendar days "
            "about AI, agentic AI, cloud, data centers, banking technology, fintech, central banks, "
            "government AI policy, and enterprise technology in the GCC. Cover central banks, local "
            "banks, global banks operating in the GCC, fintech firms, cloud service providers, "
            "government announcements, and adjacent industries. Prefer primary sources and credible "
            "business press. Exclude evergreen/background articles unless clearly labeled as context."
        ),
    )
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
