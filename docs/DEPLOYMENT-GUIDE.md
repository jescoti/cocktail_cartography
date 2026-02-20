# Deployment Guide for Cocktail Cartography

This guide covers deploying Cocktail Cartography to both production and staging environments.

## Table of Contents
- [Production Deployment (cocktail-cartography.com)](#production-deployment-cocktail-cartographycom)
- [Staging Deployment (Fly.io)](#staging-deployment-flyio)
- [Data Updates](#data-updates)
- [Troubleshooting](#troubleshooting)

---

## Production Deployment (cocktail-cartography.com)

**Host:** DreamHost
**URL:** https://cocktail-cartography.com
**Type:** Static site hosting
**Directory:** `public/`

### Prerequisites

- SSH access to DreamHost (username: `jessec1000`)
- DreamHost server: `iad1-shared-e1-34.dreamhost.com`
- Local `public/` directory with built static files

### Deployment Methods

#### Method 1: Using the Deploy Script (Recommended)

```bash
# From project root
./deploy.sh jessec1000 iad1-shared-e1-34.dreamhost.com
```

The script will:
1. Check SSH connection
2. Sync files via rsync
3. Preserve file permissions
4. Delete removed files from server

#### Method 2: Manual rsync

```bash
# Deploy all files
rsync -avz --delete public/ jessec1000@iad1-shared-e1-34.dreamhost.com:~/cocktail-cartography.com/

# Deploy only HTML updates
rsync -avz public/*.html jessec1000@iad1-shared-e1-34.dreamhost.com:~/cocktail-cartography.com/

# Deploy only data updates
rsync -avz public/data/ jessec1000@iad1-shared-e1-34.dreamhost.com:~/cocktail-cartography.com/data/
```

#### Method 3: FTP Upload

1. Connect to DreamHost via FTP client (FileZilla, Cyberduck, etc.)
2. Navigate to `/home/jessec1000/cocktail-cartography.com/`
3. Upload contents of `public/` directory
4. Ensure file permissions are 644 for files, 755 for directories

### File Structure

```
cocktail-cartography.com/
├── index.html              # Main visualization
├── about.html              # About page
├── privacy.html            # Privacy policy
├── terms.html              # Terms of service
├── reddit-callback.html    # OAuth callback
└── data/
    ├── embeddings.json     # Cocktail coordinates & recipes
    ├── taxonomy.json       # Ingredient categorization
    └── recipes.json        # Backup recipe data
```

### Important Notes

- **File Permissions:** Ensure JSON files are readable (644)
  ```bash
  ssh jessec1000@iad1-shared-e1-34.dreamhost.com "chmod 644 cocktail-cartography.com/data/*.json"
  ```

- **SSL Certificate:** Let's Encrypt SSL is enabled via DreamHost panel

- **DNS:** Domain is configured through DreamHost's nameservers

---

## Staging Deployment (Fly.io)

**Host:** Fly.io
**URL:** https://cocktail-cartography.fly.dev
**Type:** Container deployment
**Note:** Legacy staging environment, kept for reference

### Prerequisites

- Fly.io CLI installed (`fly` command)
- Authenticated with Fly.io account
- Docker installed locally (for building)

### Configuration Files

#### fly.toml
```toml
app = "cocktail-cartography"
primary_region = "sjc"

[build]

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

#### Dockerfile
```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY server.js ./
COPY viz/ ./viz/
COPY data/ ./data/
EXPOSE 3000
CMD ["node", "server.js"]
```

### Deployment Commands

```bash
# Deploy to Fly.io
fly deploy

# Check deployment status
fly status

# View logs
fly logs

# Open in browser
fly open

# Scale instances
fly scale count 1

# SSH into container
fly ssh console
```

### Adding Custom Domain (if needed)

```bash
# Add custom domain certificate
fly certs add your-domain.com

# List certificates
fly certs list

# Check certificate status
fly certs show your-domain.com
```

Then add CNAME record in your DNS:
- Type: CNAME
- Name: @ or subdomain
- Value: cocktail-cartography.fly.dev

---

## Data Updates

### Updating Cocktail Data

1. **Rebuild embeddings locally:**
   ```bash
   python scripts/build_embeddings.py
   ```

2. **Test locally:**
   ```bash
   cd public && python3 -m http.server 8888
   # Visit http://localhost:8888
   ```

3. **Deploy to production:**
   ```bash
   rsync -avz public/data/ jessec1000@iad1-shared-e1-34.dreamhost.com:~/cocktail-cartography.com/data/
   ```

### File Locations

- **Source data:** `data/ingredients.xlsx` (ingredient flavor profiles)
- **Generated files:**
  - `data/embeddings.json` - Main data file with coordinates
  - `data/taxonomy.json` - Ingredient categorization
  - `data/recipes.json` - Recipe details

---

## Troubleshooting

### Production (DreamHost)

#### Site Not Loading
- Check file permissions: `ls -la cocktail-cartography.com/`
- Verify DNS: `nslookup cocktail-cartography.com`
- Clear browser cache

#### 403 Forbidden on JSON files
```bash
ssh jessec1000@iad1-shared-e1-34.dreamhost.com
chmod 644 cocktail-cartography.com/data/*.json
```

#### SSH Connection Issues
- Verify SSH key is added: `ssh-add -l`
- Check SSH config: `~/.ssh/config`
- Test connection: `ssh -v jessec1000@iad1-shared-e1-34.dreamhost.com`

### Staging (Fly.io)

#### Deployment Fails
```bash
# Check app status
fly status

# View detailed logs
fly logs --verbose

# Restart app
fly apps restart cocktail-cartography
```

#### Container Won't Start
- Check `package.json` dependencies
- Verify `server.js` exists
- Review Dockerfile for issues

---

## Workflow Summary

### Production Deployment Checklist

- [ ] Test changes locally: `cd public && python3 -m http.server 8888`
- [ ] Run deployment: `./deploy.sh jessec1000 iad1-shared-e1-34.dreamhost.com`
- [ ] Verify site loads: https://cocktail-cartography.com
- [ ] Check browser console for errors
- [ ] Test ingredient filtering works
- [ ] Verify all pages accessible (about, privacy, terms)

### Quick Commands Reference

```bash
# Deploy to production
./deploy.sh jessec1000 iad1-shared-e1-34.dreamhost.com

# Deploy to staging (Fly.io)
fly deploy

# Fix permissions on production
ssh jessec1000@iad1-shared-e1-34.dreamhost.com "chmod -R 755 cocktail-cartography.com/"
ssh jessec1000@iad1-shared-e1-34.dreamhost.com "chmod 644 cocktail-cartography.com/data/*.json"

# View production files
ssh jessec1000@iad1-shared-e1-34.dreamhost.com "ls -la cocktail-cartography.com/"

# Local testing
cd public && python3 -m http.server 8888
```

---

## Architecture Notes

### Why Two Deployment Methods?

1. **Production (Static):** Optimal for performance, cost, and reliability
   - No server process to manage
   - Instant response times
   - Lower hosting costs
   - Better uptime

2. **Staging (Container):** Legacy from initial development
   - Useful for testing server-side features
   - Platform-agnostic deployment
   - Easy rollback capability
   - Kept for potential future needs

### Migration Path

The project migrated from container-based (Fly.io) to static hosting (DreamHost) because:
- All filtering/interaction happens client-side
- No server-side processing needed
- Static hosting is more cost-effective
- Simplified maintenance

---

## Contact & Support

- **DreamHost Support:** Via DreamHost panel
- **Fly.io Support:** https://fly.io/docs
- **Project Issues:** https://github.com/cotarij/cocktail_cartography/issues

---

*Last updated: February 2026*