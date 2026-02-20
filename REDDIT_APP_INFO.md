# Reddit App Registration Information

## For Reddit App Registration (https://www.reddit.com/prefs/apps)

### Required Information:

**App Name:** Cocktail Cartography Recipe Extractor

**App Type:** Choose "script" if just for personal use, or "web app" if others will use it

**Description:**
```
Tool for extracting and analyzing cocktail recipes from Reddit communities like r/cocktails.
Used to build a comprehensive cocktail database with proper attribution to original creators.
```

**About URL:** https://cocktail-cartography.com/about.html

**Redirect URI:** https://cocktail-cartography.com/reddit-callback.html

**Permissions Needed:** Read access to public posts

### Compliance Documentation:

✅ **Privacy Policy:** https://cocktail-cartography.com/privacy.html
✅ **Terms of Service:** https://cocktail-cartography.com/terms.html
✅ **About Page:** https://cocktail-cartography.com/about.html
✅ **OAuth Callback:** https://cocktail-cartography.com/reddit-callback.html

### What These Pages Do:

1. **Privacy Policy** - Explains:
   - We only access public Reddit posts
   - No personal data is stored
   - Compliance with Reddit's Responsible Builder Policy
   - User rights and data handling

2. **Terms of Service** - Covers:
   - Reddit API compliance
   - User responsibilities
   - Legal disclaimers
   - Intellectual property respect

3. **About Page** - Describes:
   - Project purpose
   - Reddit integration features
   - Links to privacy/terms

4. **Reddit Callback** - Handles:
   - OAuth redirect from Reddit
   - Displays authorization code
   - Shows any errors

### How the OAuth Flow Works:

1. Your script directs user to Reddit's authorization URL
2. User approves access
3. Reddit redirects to: https://cocktail-cartography.com/reddit-callback.html?code=AUTH_CODE
4. The callback page displays the auth code
5. Your script exchanges the code for an access token
6. Use the token to access Reddit's API

### Reddit API Best Practices:

- **Rate Limiting:** Stay within Reddit's limits (60 requests per minute)
- **User-Agent:** Include descriptive user-agent string
- **Attribution:** Credit original posters when using their content
- **Respect Removals:** Don't store deleted/removed content
- **Follow Rules:** Respect subreddit rules and moderator actions

### Example User-Agent String:
```
script:cocktail-cartography:v1.0.0 (by /u/YOUR_REDDIT_USERNAME)
```

### Important Notes:

- Replace YOUR_REDDIT_USERNAME with your actual Reddit username
- Use HTTPS for all URLs (not HTTP)
- The redirect URI must match EXACTLY what you register
- Keep your client secret secure - never commit it to git

## Need Help?

- Reddit API Docs: https://www.reddit.com/dev/api
- OAuth2 Guide: https://github.com/reddit-archive/reddit/wiki/OAuth2
- Rate Limits: https://www.reddit.com/wiki/api