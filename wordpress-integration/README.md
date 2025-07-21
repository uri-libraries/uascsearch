# WordPress Plugin Installation Guide

## Installation Options

### Option 1: Full JavaScript Plugin (Standard)
For sites that allow JavaScript and custom plugins.

### Option 2: PHP-Only Plugin (Locked-Down Sites)
For sites that restrict JavaScript but allow PHP plugins.

### Option 3: Simple Link Plugin (Highly Restricted Sites)
For sites that only allow basic shortcodes.

---

## Option 1: Full JavaScript Plugin

### Quick Installation

#### Step 1: Download Plugin Files
Download these files from the `wordpress-integration/` folder:
- `uri-xml-search.php`
- `uri-xml-search.js`
- `uri-xml-search.css`
- `search-results-template.php`

#### Step 2: Upload to WordPress
1. Access your WordPress site files via FTP, cPanel File Manager, or hosting control panel
2. Navigate to `/wp-content/plugins/`
3. Create a new folder called `uri-xml-search`
4. Upload all 4 files to `/wp-content/plugins/uri-xml-search/`

#### Step 3: Activate Plugin
1. Log into WordPress Admin Dashboard
2. Go to **Plugins** → **Installed Plugins**
3. Find "URI XML Search" and click **Activate**

#### Step 4: Configure API Settings
1. Go to **Settings** → **URI XML Search**
2. Enter your Django API URL:
   - Development: `http://127.0.0.1:8000`
   - Production: `https://your-domain.com`
3. Click **Save Changes**

#### Step 5: Add Search Box to Page
1. Edit the page where you want the search box
2. Add this shortcode:
   ```
   [uri_xml_search placeholder="Search manuscripts and archives..." button_text="Search Archives"]
   ```
3. **Save** the page

#### Step 6: Test the Search
1. Visit the page with the search box
2. Enter a search term (e.g., "history")
3. Click "Search Archives"
4. You should see results on the `/xml-search-results/` page

---

## Option 2: PHP-Only Plugin (No JavaScript)

**Best for locked-down WordPress sites that restrict JavaScript**

### Features
- ✅ No JavaScript required
- ✅ Works on locked-down WordPress sites
- ✅ Search results display on same page
- ✅ Pagination support
- ✅ Responsive design
- ✅ SEO-friendly server-side rendering

### Installation Steps

#### Step 1: Download Plugin Files
Download these files from the `wordpress-integration/` folder:
- `uri-xml-search-nojs.php`
- `uri-xml-search-nojs.css`

#### Step 2: Upload to WordPress
1. Access your WordPress site files
2. Navigate to `/wp-content/plugins/`
3. Create a new folder called `uri-xml-search-nojs`
4. Upload both files to `/wp-content/plugins/uri-xml-search-nojs/`

#### Step 3: Activate Plugin
1. Log into WordPress Admin Dashboard
2. Go to **Plugins** → **Installed Plugins**
3. Find "URI XML Search (No JS)" and click **Activate**

#### Step 4: Configure API Settings
1. Go to **Settings** → **URI XML Search**
2. Enter your Django API URL:
   - Development: `http://127.0.0.1:8000`
   - Production: `https://your-domain.com`
3. Click **Save Changes**

#### Step 5: Add Search Box to Page
1. Edit the page where you want the search box
2. Add this shortcode:
   ```
   [uri_xml_search placeholder="Search manuscripts and archives..." button_text="Search Archives"]
   ```
3. **Save** the page

#### Step 6: Test the Search
1. Visit the page with the search box
2. Enter a search term (e.g., "history")
3. Click "Search Archives"
4. Results will appear on the same page below the search box

### How to Present to Administrators
> "This plugin uses only server-side PHP code (no JavaScript) and makes secure HTTP requests to our Django API. It's similar to how WordPress itself fetches external content like RSS feeds or plugin updates. The plugin is self-contained and doesn't execute any client-side code."

---

## Option 3: Simple Link Plugin (Highly Restricted)

**For sites that only allow basic shortcodes and restrict custom plugins**

### Features
- ✅ Minimal code footprint
- ✅ Only creates a styled link
- ✅ Links to external search page
- ✅ No API calls from WordPress

### Installation Steps

#### Step 1: Download Plugin File
Download this file from the `wordpress-integration/` folder:
- `xml-search-link.php`

#### Step 2: Upload to WordPress
1. Access your WordPress site files
2. Navigate to `/wp-content/plugins/`
3. Create a new folder called `xml-search-link`
4. Upload `xml-search-link.php` to `/wp-content/plugins/xml-search-link/`

#### Step 3: Activate Plugin
1. Log into WordPress Admin Dashboard
2. Go to **Plugins** → **Installed Plugins**
3. Find "URI XML Search Link" and click **Activate**

#### Step 4: Add Search Link to Page
1. Edit the page where you want the search link
2. Add this shortcode:
   ```
   [xml_search_link url="https://your-domain.com/xml-search/" text="Search XML Archives"]
   ```
3. **Save** the page

#### Step 5: Create External Search Page
1. Upload `standalone-search.html` to your web server
2. Update the `API_BASE_URL` in the HTML file to point to your Django API
3. Update the shortcode URL to point to this HTML file

### Alternative: Direct Link
If you can't install plugins at all, just add a regular HTML link:
```html
<a href="https://your-domain.com/xml-search/" target="_blank" class="search-button">Search XML Archives</a>
```

---

## Which Option Should You Choose?

### Use JavaScript Plugin If:
- You have full control over the WordPress site
- JavaScript is allowed
- You want the best user experience
- You need the results integrated into WordPress

### Use PHP-Only Plugin If:
- JavaScript is restricted but PHP plugins are allowed
- You want results on the same page
- You need SEO-friendly server-side rendering
- Site administrators are concerned about client-side code

### Use Link Plugin If:
- The site is heavily locked down
- Only basic shortcodes are allowed
- You can host the search page externally
- You want the simplest possible integration
- Pagination for large result sets
- Direct links to original XML files
- File metadata (size, modification date)
- Error handling and loading states
- Mobile-friendly responsive design

## Customization Options

### Use Link Plugin If:
- The site is heavily locked down
- Only basic shortcodes are allowed
- You can host the search page externally
- You want the simplest possible integration

---

## Troubleshooting

### Plugin Not Appearing
- Check that all files are uploaded to the correct plugin folder
- Verify file permissions (755 for folders, 644 for files)
- Ensure the main plugin file is named correctly

### 404 Error on Results Page (JavaScript Plugin Only)
- Go to **Settings** → **Permalinks**
- Click **Save Changes** (this refreshes the URL rewrite rules)

### No Search Results
- Check that your Django API is running and accessible
- Verify the API URL in plugin settings
- Test the API directly: `curl "http://your-api.com/search/?q=test"`
- Check WordPress error logs for API connection issues

### Search Box Not Displaying
- Make sure you've added the correct shortcode
- Check that the plugin is activated
- Verify there are no PHP errors in the error logs

### CORS Issues
- Ensure your WordPress domain is added to Django's `CORS_ALLOWED_ORIGINS`
- Check that your Django server is accessible from the WordPress server

---

## Customization

### Shortcode Options

#### JavaScript Plugin
```
[uri_xml_search placeholder="Custom search text" button_text="Search Now"]
```

#### PHP-Only Plugin
```
[uri_xml_search placeholder="Search manuscripts..." button_text="Search Archives" results_per_page="15"]
```

#### Link Plugin
```
[xml_search_link url="https://your-search-page.com" text="Search Archives" class="custom-button"]
```

### Styling
- **JavaScript Plugin**: Edit `uri-xml-search.css`
- **PHP-Only Plugin**: Edit `uri-xml-search-nojs.css`
- **Link Plugin**: Add custom CSS to your theme

### Results Display
- **JavaScript Plugin**: Modify `search-results-template.php`
- **PHP-Only Plugin**: Results display inline - modify the plugin's `display_search_results` method
- **Link Plugin**: Customize `standalone-search.html`

---

## File Structure

### JavaScript Plugin
```
/wp-content/plugins/uri-xml-search/
├── uri-xml-search.php          # Main plugin file
├── uri-xml-search.js           # JavaScript functionality
├── uri-xml-search.css          # Styling
└── search-results-template.php # Results page template
```

### PHP-Only Plugin
```
/wp-content/plugins/uri-xml-search-nojs/
├── uri-xml-search-nojs.php     # Main plugin file
└── uri-xml-search-nojs.css     # Styling
```

### Link Plugin
```
/wp-content/plugins/xml-search-link/
└── xml-search-link.php         # Main plugin file
```

---

## Support
If you encounter issues:
1. Check the troubleshooting section above
2. Review the main README.md for detailed documentation
3. Test your Django API independently
4. Check WordPress error logs
5. Contact the development team

## Troubleshooting

### Common Issues
1. **Search returns no results**: Check that your Django server is running and accessible
2. **CORS errors**: Ensure your WordPress domain is added to Django's CORS settings
3. **404 on results page**: Go to WordPress Admin → Settings → Permalinks and click "Save Changes"

### Debug Mode
Add this to your WordPress wp-config.php for debugging:
```php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
```

## Production Deployment

### Django Server
1. Deploy your Django application to a production server
2. Update the API URL in WordPress settings
3. Ensure CORS is properly configured for your domain

### Security
- Use HTTPS for both WordPress and Django
- Implement rate limiting on the Django API
- Consider adding authentication if needed

### Performance
- Enable caching on the Django side
- Consider using a CDN for static assets
- Monitor API response times

---

## Updated Features
- **Improved Title Decoding**: Titles now decode URL-encoded characters (e.g., `%20` becomes a space).
- **Enhanced Snippet Generation**: Snippets are extracted from specific fields (`Creator`, `Title`, `Dates`, `Abstract`) for more relevant search results.
