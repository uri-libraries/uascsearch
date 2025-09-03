<?php
/**
 * Plugin Name: URI XML Search (No JS)
 * Description: Server-side XML search for locked-down WordPress sites
 * Version: 1.0
 * Author: URI Libraries
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class URIXMLSearchNoJS {
    
    private $api_base_url;
    
    public function __construct() {
        $this->api_base_url = get_option('uri_xml_search_api_url', 'https://uascsearch.library.uri.edu');
        
        add_action('wp_enqueue_scripts', array($this, 'enqueue_styles'));
        add_shortcode('uri_xml_search', array($this, 'search_shortcode'));
        add_action('admin_menu', array($this, 'admin_menu'));
        
        // Handle search processing
        add_action('init', array($this, 'handle_search'));
    }
    
    public function enqueue_styles() {
        wp_enqueue_style('uri-xml-search', plugin_dir_url(__FILE__) . 'uri-xml-search-nojs.css', array(), '1.0');
    }
    
    public function search_shortcode($atts) {
        $atts = shortcode_atts(array(
            'placeholder' => 'Search XML archives...',
            'button_text' => 'Search',
            'results_per_page' => 10
        ), $atts);
        
        $query = sanitize_text_field($_GET['q'] ?? '');
        $page = intval($_GET['search_page'] ?? 1);
        
        ob_start();
        ?>
        <div class="uri-xml-search-container">
            <!-- Search Form -->
            <form class="uri-xml-search-form" method="get">
                <div class="search-input-group">
                    <input type="text" 
                           name="q" 
                           class="uri-xml-search-input" 
                           placeholder="<?php echo esc_attr($atts['placeholder']); ?>"
                           value="<?php echo esc_attr($query); ?>"
                           required>
                    <button type="submit" class="uri-xml-search-button">
                        <?php echo esc_html($atts['button_text']); ?>
                    </button>
                </div>
                <?php 
                // Preserve other GET parameters
                foreach ($_GET as $key => $value) {
                    if ($key !== 'q' && $key !== 'search_page') {
                        echo '<input type="hidden" name="' . esc_attr($key) . '" value="' . esc_attr($value) . '">';
                    }
                }
                ?>
            </form>
            
            <?php if ($query): ?>
                <div class="uri-xml-search-results">
                    <?php echo $this->display_search_results($query, $page, $atts['results_per_page']); ?>
                </div>
            <?php endif; ?>
        </div>
        <?php
        return ob_get_clean();
    }
    
    private function display_search_results($query, $page, $per_page) {
        $api_url = $this->api_base_url . '/search/?q=' . urlencode($query) . '&page=' . $page . '&per_page=' . $per_page;
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/json'
            )
        ));
        
        if (is_wp_error($response)) {
            return '<div class="uri-xml-error">Search service temporarily unavailable. Please try again later.</div>';
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if (!$data || !isset($data['results'])) {
            return '<div class="uri-xml-error">Invalid response from search service.</div>';
        }
        
        $html = '';
        
        if ($data['count'] === 0) {
            $html .= '<div class="uri-xml-no-results">No results found for "' . esc_html($query) . '"</div>';
        } else {
            $html .= '<div class="uri-xml-results-header">';
            $html .= '<h3>Search Results for "' . esc_html($query) . '"</h3>';
            $html .= '<p class="uri-xml-results-count">Found ' . $data['count'] . ' result(s)</p>';
            $html .= '</div>';
            
            $html .= '<div class="uri-xml-results-list">';
            
            foreach ($data['results'] as $result) {
                $html .= '<div class="uri-xml-result-item">';
                $html .= '<h4 class="uri-xml-result-title">';
                
                // Use the clean title instead of filename and handle <mark> tags
                $display_title = !empty($result['title']) ? $result['title'] : urldecode($result['filename']);
                // Convert <mark> tags to <strong> tags for bold highlighting in titles too
                $display_title = str_replace('<mark>', '<strong>', $display_title);
                $display_title = str_replace('</mark>', '</strong>', $display_title);
                $html .= '<a href="' . esc_url($result['url']) . '" target="_blank">' . wp_kses($display_title, array('strong' => array())) . '</a>';
                
                $html .= '</h4>';
                
                // Optionally show filename as metadata if it's different from title
                if (!empty($result['title']) && $result['title'] !== urldecode($result['filename'])) {
                    $html .= '<p class="uri-xml-filename">File: ' . esc_html(urldecode($result['filename'])) . '</p>';
                }
                
                // Convert <mark> tags to <strong> tags for bold highlighting and allow HTML rendering
                $snippet = str_replace('<mark>', '<strong>', $result['snippet']);
                $snippet = str_replace('</mark>', '</strong>', $snippet);
                $html .= '<p class="uri-xml-result-snippet">' . wp_kses($snippet, array('strong' => array())) . '</p>';
                $html .= '<div class="uri-xml-result-meta">';
                $html .= '<span class="uri-xml-file-size">Size: ' . $this->format_file_size($result['file_size']) . '</span>';
                if (!empty($result['last_modified'])) {
                    $html .= '<span class="uri-xml-last-modified">Modified: ' . esc_html(date('M j, Y', strtotime($result['last_modified']))) . '</span>';
                }
                $html .= '</div>';
                $html .= '</div>';
            }
            
            $html .= '</div>';
            
            // Add pagination
            if ($data['total_pages'] > 1) {
                $html .= $this->generate_pagination($query, $data['page'], $data['total_pages']);
            }
        }
        
        return $html;
    }
    
    private function generate_pagination($query, $current_page, $total_pages) {
        $html = '<div class="uri-xml-pagination">';
        
        // Previous page
        if ($current_page > 1) {
            $prev_url = add_query_arg(array('q' => $query, 'search_page' => $current_page - 1));
            $html .= '<a href="' . esc_url($prev_url) . '" class="uri-xml-page-link">‹ Previous</a>';
        }
        
        // Page numbers
        $start = max(1, $current_page - 2);
        $end = min($total_pages, $current_page + 2);
        
        for ($i = $start; $i <= $end; $i++) {
            if ($i === $current_page) {
                $html .= '<span class="uri-xml-page-current">' . $i . '</span>';
            } else {
                $page_url = add_query_arg(array('q' => $query, 'search_page' => $i));
                $html .= '<a href="' . esc_url($page_url) . '" class="uri-xml-page-link">' . $i . '</a>';
            }
        }
        
        // Next page
        if ($current_page < $total_pages) {
            $next_url = add_query_arg(array('q' => $query, 'search_page' => $current_page + 1));
            $html .= '<a href="' . esc_url($next_url) . '" class="uri-xml-page-link">Next ›</a>';
        }
        
        $html .= '</div>';
        
        return $html;
    }
    
    private function format_file_size($bytes) {
        if ($bytes === 0) return '0 Bytes';
        $k = 1024;
        $sizes = array('Bytes', 'KB', 'MB', 'GB');
        $i = floor(log($bytes) / log($k));
        return round($bytes / pow($k, $i), 2) . ' ' . $sizes[$i];
    }
    
    public function handle_search() {
        // This method can be used for additional search processing if needed
    }
    
    public function admin_menu() {
        add_options_page(
            'URI XML Search Settings',
            'URI XML Search',
            'manage_options',
            'uri-xml-search-nojs',
            array($this, 'admin_page')
        );
    }
    
    public function admin_page() {
        if (isset($_POST['submit'])) {
            update_option('uri_xml_search_api_url', sanitize_text_field($_POST['api_url']));
            echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
        }
        
        $api_url = get_option('uri_xml_search_api_url', 'https://uascsearch.library.uri.edu');
        ?>
        <div class="wrap">
            <h1>URI XML Search Settings</h1>
            <form method="post">
                <table class="form-table">
                    <tr>
                        <th scope="row">API Base URL</th>
                        <td>
                            <input type="url" name="api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
                            <p class="description">The base URL of your Django API (e.g., https://uascsearch.library.uri.edu)</p>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            
            <h2>Usage</h2>
            <p>Add this shortcode to any page or post:</p>
            <code>[uri_xml_search placeholder="Search manuscripts..." button_text="Search"]</code>
        
        </div>
        <?php
    }
}

// Initialize the plugin
new URIXMLSearchNoJS();
?>
