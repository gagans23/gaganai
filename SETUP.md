# Free Hosting, Subscribers, Tracking, and Domain

The site is already hosted for free on GitHub Pages:

https://gagans23.github.io/gaganai/

## Domain

Target domain:

```text
gagansachdeva.com
```

Buy the domain first from a registrar that supports `.ai` domains. After you own it, add these DNS records at the
registrar:

```text
Type: A
Name: @
Value: 185.199.108.153

Type: A
Name: @
Value: 185.199.109.153

Type: A
Name: @
Value: 185.199.110.153

Type: A
Name: @
Value: 185.199.111.153

Type: CNAME
Name: www
Value: gagans23.github.io
```

Then add this file to the repo:

```text
CNAME
```

with:

```text
gagansachdeva.com
```

Finally, enable the custom domain in GitHub Pages settings.

## Subscriber Collection

The site is wired for Buttondown with this username:

```text
gaganai
```

Create the Buttondown newsletter at:

https://buttondown.email

Use `gaganai` as the newsletter username if available. If you choose a different username, update:

```text
assets/site-config.js
```

Change:

```js
buttondownUsername: "gaganai"
```

## Tracking

The site is wired for Cloudflare Web Analytics. Create a free Cloudflare Web Analytics site and paste the token into:

```text
assets/site-config.js
```

Change:

```js
cloudflareAnalyticsToken: ""
```

to:

```js
cloudflareAnalyticsToken: "YOUR_TOKEN"
```

Then commit and push:

```bash
git add .
git commit -m "Configure subscribers and analytics"
git push
```

## What You Will See

Buttondown:
- email subscribers
- confirmed/unconfirmed status
- newsletter sends

Cloudflare Web Analytics:
- page views
- visitors
- top pages
- referrers
- countries
- device/browser signals
