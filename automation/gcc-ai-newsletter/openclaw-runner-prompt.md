# OpenClaw Scheduled Runner: GCC AI Daily

Run the local GCC AI newsletter factory.

Execute:

```bash
cd /path/to/gaganai-site
./gcc-ai-newsletter/run_today.sh
```

Then reply with:

1. Source count.
2. Whether a fresh publishable issue was created or whether the system refused to force stale news.
3. Paths to:
   - LinkedIn text
   - WhatsApp text
   - source JSON
   - image prompt
4. Any errors or missing credentials.

Do not post to LinkedIn.
Do not send WhatsApp messages.
Do not invent missing news.
