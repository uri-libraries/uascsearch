# URI XML Search WordPress Integration

## Installation Instructions

### Step 1: Upload Plugin Files
1. Create a new directory: `/wp-content/plugins/uri-xml-search/`
2. Upload these files to that directory:
   - `uri-xml-search.php`
   - `uri-xml-search.js`
   - `uri-xml-search.css`
   - `search-results-template.php`

### Step 2: Activate the Plugin
1. Go to WordPress Admin → Plugins
2. Find "URI XML Search" and click "Activate"

### Step 3: Configure the Plugin
1. Go to WordPress Admin → Settings → URI XML Search
2. Set the API Base URL to your Django server:
   - For development: `http://127.0.0.1:8000`
   - For production: `https://your-django-domain.com`
3. Save the settings

### Step 4: Add Search Box to Your Page
1. Edit the page: https://web.uri.edu/specialcollections/manuscripts_list2/
2. Add this shortcode where you want the search box to appear:
   ```
   [uri_xml_search placeholder="Search manuscripts and archives..." button_text="Search Archives"]
   ```

### Step 5: Test the Integration
1. Visit the page with the search box
2. Enter a search term (e.g., "history", "college", "manuscripts")
3. Click "Search Archives"
4. You should be redirected to a results page showing matching XML files

## How It Works

### Search Process
1. User enters search term in the search box
2. Form submits to `/xml-search-results/` page
3. JavaScript loads and calls your Django API
4. Results are displayed in a formatted, user-friendly way

### URL Structure
- Search box page: `https://web.uri.edu/specialcollections/manuscripts_list2/`
- Results page: `https://web.uri.edu/xml-search-results/?q=search_term`

### Features
- Clean, responsive design matching WordPress theme
- Pagination for large result sets
- Direct links to original XML files
- File metadata (size, modification date)
- Error handling and loading states
- Mobile-friendly responsive design

## Customization Options

### Search Box Appearance
You can customize the search box using shortcode parameters:
```
[uri_xml_search placeholder="Custom placeholder text" button_text="Custom button text"]
```

### Styling
Edit `uri-xml-search.css` to match your site's design:
- Colors can be changed by modifying the CSS variables
- Font sizes and spacing can be adjusted
- The design is fully responsive

### Results Page
The results page template can be customized by editing `search-results-template.php`:
- Modify the HTML structure
- Add custom branding or navigation
- Integrate with your theme's specific design elements

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
