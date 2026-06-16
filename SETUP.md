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

View traffic in Cloudflare:

```text
Cloudflare Dashboard
→ gagansachdeva.com
→ Analytics & Logs
→ Web Analytics
```

Use Web Analytics rather than only Cloudflare traffic analytics for this site because GitHub Pages is the origin and
Cloudflare may not proxy every request unless the DNS records are orange-clouded.

## Comments And Likes

The site is static, so it cannot store comments or likes by itself. Best options:

- Giscus for article comments using GitHub Discussions.
- LinkedIn discussion links below each article after you publish the article on LinkedIn.
- Buttondown replies for newsletter subscribers.

The current articles include a reader-response box with:

```text
gaganstx@gmail.com
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
