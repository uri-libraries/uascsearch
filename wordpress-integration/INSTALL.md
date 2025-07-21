# WordPress Plugin Installation Guide

## Quick Installation

### Step 1: Download Plugin Files
Download these files from the `wordpress-integration/` folder:
- `uri-xml-search.php`
- `uri-xml-search.js`
- `uri-xml-search.css`
- `search-results-template.php`

### Step 2: Upload to WordPress
1. Access your WordPress site files via FTP, cPanel File Manager, or hosting control panel
2. Navigate to `/wp-content/plugins/`
3. Create a new folder called `uri-xml-search`
4. Upload all 4 files to `/wp-content/plugins/uri-xml-search/`

### Step 3: Activate Plugin
1. Log into WordPress Admin Dashboard
2. Go to **Plugins** → **Installed Plugins**
3. Find "URI XML Search" and click **Activate**

### Step 4: Configure API Settings
1. Go to **Settings** → **URI XML Search**
2. Enter your Django API URL:
   - Development: `http://127.0.0.1:8000`
   - Production: `https://your-domain.com`
3. Click **Save Changes**

### Step 5: Add Search Box to Page
1. Edit the page where you want the search box
2. Add this shortcode:
   ```
   [uri_xml_search placeholder="Search manuscripts and archives..." button_text="Search Archives"]
   ```
3. **Save** the page

### Step 6: Test the Search
1. Visit the page with the search box
2. Enter a search term (e.g., "history")
3. Click "Search Archives"
4. You should see results on the `/xml-search-results/` page

## Troubleshooting

### Plugin Not Appearing
- Check that all files are uploaded to `/wp-content/plugins/uri-xml-search/`
- Verify file permissions (755 for folders, 644 for files)

### 404 Error on Results Page
- Go to **Settings** → **Permalinks**
- Click **Save Changes** (this refreshes the URL rewrite rules)

### No Search Results
- Check that your Django API is running and accessible
- Verify the API URL in plugin settings
- Test the API directly: `curl "http://your-api.com/search/?q=test"`

### Search Box Not Displaying
- Make sure you've added the shortcode: `[uri_xml_search]`
- Check that the plugin is activated
- Look for JavaScript errors in browser console

## Customization

### Shortcode Options
```
[uri_xml_search placeholder="Custom search text" button_text="Search Now"]
```

### Styling
Edit `uri-xml-search.css` to match your site's design:
- Change colors by modifying CSS color values
- Adjust spacing and fonts
- Customize the results page appearance

### Results Page
Modify `search-results-template.php` to:
- Match your theme's layout
- Add custom branding
- Include additional navigation

## Updated Features
- **Improved Title Decoding**: Titles now decode URL-encoded characters (e.g., `%20` becomes a space).
- **Enhanced Snippet Generation**: Snippets are extracted from specific fields (`Creator`, `Title`, `Dates`, `Abstract`) for more relevant search results.

## File Structure
```
/wp-content/plugins/uri-xml-search/
├── uri-xml-search.php          # Main plugin file
├── uri-xml-search.js           # JavaScript functionality
├── uri-xml-search.css          # Styling
└── search-results-template.php # Results page template
```

## Support
If you encounter issues:
1. Check the troubleshooting section above
2. Review the main README.md for detailed documentation
3. Contact the development team
