# DreamHost Deployment Guide for Cocktail Cartography

This guide explains how to deploy the Cocktail Cartography visualization to DreamHost as a static website.

## Prerequisites

- DreamHost hosting account with cocktail-cartography.com domain
- FTP/SFTP access credentials or SSH access to your DreamHost server
- The `public/` directory contains all necessary files for deployment

## File Structure

The `public/` directory contains everything needed for the static site:
```
public/
├── index.html          # Main visualization page
├── data/
│   ├── embeddings.json # Cocktail coordinates and recipe data
│   ├── recipes.json    # Backup recipe data
│   └── taxonomy.json   # Ingredient categorization
└── (any other assets)
```

## Deployment Methods

### Method 1: FTP/SFTP Upload (Simplest)

1. Connect to your DreamHost server using an FTP client (FileZilla, Cyberduck, etc.)
2. Navigate to your domain's web root directory (usually `/home/username/cocktail-cartography.com/`)
3. Upload the entire contents of the `public/` directory (not the directory itself)
4. Ensure the structure looks like:
   ```
   cocktail-cartography.com/
   ├── index.html
   ├── data/
   │   ├── embeddings.json
   │   ├── recipes.json
   │   └── taxonomy.json
   ```

### Method 2: SSH and rsync (Faster for updates)

1. SSH into your DreamHost server:
   ```bash
   ssh username@cocktail-cartography.com
   ```

2. From your local machine, use rsync to sync files:
   ```bash
   rsync -avz --delete public/ username@cocktail-cartography.com:~/cocktail-cartography.com/
   ```

### Method 3: Git Deployment (If DreamHost supports it)

1. SSH into your DreamHost server
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/cocktail_cartography.git temp
   ```
3. Copy the public directory contents:
   ```bash
   cp -r temp/public/* ~/cocktail-cartography.com/
   ```

## Verification

After deployment, verify the site works by:

1. Visit https://cocktail-cartography.com
2. Check that the visualization loads
3. Test the ingredient filtering panel
4. Verify tooltips work when hovering over cocktails

## Updating Content

To update the cocktail data or visualization:

1. Make changes locally in the repository
2. Test locally with: `python3 -m http.server 8000` in the `public/` directory
3. Re-upload the changed files using one of the methods above

## Troubleshooting

### Site Not Loading
- Check file permissions (should be 644 for files, 755 for directories)
- Verify index.html is in the root directory
- Clear browser cache

### Data Not Loading
- Check browser console for errors (F12)
- Verify data files are uploaded and paths are correct
- Ensure JSON files are valid

### CORS Issues
- Should not occur with static hosting
- If issues arise, contact DreamHost support about CORS headers

## Domain Configuration

If your domain isn't pointing to the correct directory:

1. Log into DreamHost panel
2. Navigate to "Manage Domains"
3. Edit cocktail-cartography.com
4. Set the web directory to the correct path

## Performance Optimization (Optional)

Consider enabling in DreamHost panel:
- Gzip compression for .json files
- Browser caching headers
- CloudFlare CDN (if available)

## Support

For DreamHost-specific issues, contact their support.
For application issues, check the repository issues page.