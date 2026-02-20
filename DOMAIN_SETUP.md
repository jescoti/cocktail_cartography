# Domain Configuration for cocktail-cartography.com

## DreamHost Panel Configuration

1. **Log into DreamHost Panel**
   - Go to https://panel.dreamhost.com

2. **Navigate to Domains**
   - Click "Manage Domains" in the left sidebar
   - Find `cocktail-cartography.com` in your domain list

3. **Configure Web Hosting**
   - Click "Manage" next to your domain
   - Under "Web Hosting", ensure it's set to "Fully Hosted"
   - Set the Web directory to: `/home/[username]/cocktail-cartography.com`
   - Enable "Remove www" if you want cocktail-cartography.com only (no www prefix)

4. **SSL Certificate (Important for HTTPS)**
   - In the domain settings, find "Secure Hosting"
   - Enable "Let's Encrypt SSL/TLS Certificate" (free)
   - This will automatically provision an SSL certificate

## DNS Configuration

If your domain was purchased through DreamHost, DNS should be configured automatically.

If purchased elsewhere, point your domain to DreamHost:

### Nameservers (Recommended)
Change your domain's nameservers to:
- ns1.dreamhost.com
- ns2.dreamhost.com
- ns3.dreamhost.com

### Or use A Records
Point to DreamHost's IP (you can find this in panel):
- A Record: @ → [DreamHost IP]
- A Record: www → [DreamHost IP]

## Testing Your Domain

After configuration, test your domain:

```bash
# Check DNS propagation
nslookup cocktail-cartography.com

# Test HTTP redirect to HTTPS
curl -I http://cocktail-cartography.com

# Test HTTPS
curl -I https://cocktail-cartography.com
```

## Deployment Structure

Your DreamHost directory should look like:
```
/home/[username]/
└── cocktail-cartography.com/
    ├── index.html
    ├── data/
    │   ├── embeddings.json
    │   ├── recipes.json
    │   └── taxonomy.json
    └── (any other assets)
```

## Alternative: Point to Fly.io

If you prefer to keep using Fly.io hosting with your custom domain:

1. **In Fly.io:**
   ```bash
   fly certs add cocktail-cartography.com
   ```
   This will give you a CNAME target like `cocktail-cartography.fly.dev`

2. **In DreamHost DNS:**
   - Add CNAME record: @ → cocktail-cartography.fly.dev
   - Add CNAME record: www → cocktail-cartography.fly.dev

3. **Verify Certificate:**
   ```bash
   fly certs show cocktail-cartography.com
   ```

## Troubleshooting

### Domain Not Loading
- DNS changes can take 24-48 hours to propagate
- Clear browser cache and try incognito mode
- Check DreamHost panel for any error messages

### SSL Certificate Issues
- Let's Encrypt certificates can take up to 30 minutes to provision
- Ensure domain is pointing to DreamHost before enabling SSL
- Try disabling and re-enabling SSL in panel

### Files Not Showing
- Check file permissions (644 for files, 755 for directories)
- Verify you uploaded to the correct directory
- Check `.htaccess` file isn't blocking access

## Support Contacts

- **DreamHost Support:** https://panel.dreamhost.com/support
- **Domain Issues:** Check WHOIS info at https://whois.domaintools.com
- **SSL Status:** Test at https://www.ssllabs.com/ssltest/