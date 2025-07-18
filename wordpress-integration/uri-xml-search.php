<?php
/**
 * Plugin Name: URI XML Search
 * Description: Search functionality for URI Special Collections XML archives
 * Version: 1.0
 * Author: URI Libraries
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class URIXMLSearch {
    
    private $api_base_url;
    
    public function __construct() {
        $this->api_base_url = get_option('uri_xml_search_api_url', 'http://127.0.0.1:8000');
        
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_shortcode('uri_xml_search', array($this, 'search_shortcode'));
        add_action('wp_ajax_uri_xml_search', array($this, 'ajax_search'));
        add_action('wp_ajax_nopriv_uri_xml_search', array($this, 'ajax_search'));
        add_action('admin_menu', array($this, 'admin_menu'));
        
        // Add rewrite rules for search results page
        add_action('init', array($this, 'add_rewrite_rules'));
        add_filter('query_vars', array($this, 'add_query_vars'));
        add_action('template_redirect', array($this, 'template_redirect'));
    }
    
    public function enqueue_scripts() {
        wp_enqueue_script('uri-xml-search', plugin_dir_url(__FILE__) . 'uri-xml-search.js', array('jquery'), '1.0', true);
        wp_enqueue_style('uri-xml-search', plugin_dir_url(__FILE__) . 'uri-xml-search.css', array(), '1.0');
        
        wp_localize_script('uri-xml-search', 'uri_xml_search', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('uri_xml_search_nonce'),
            'api_url' => $this->api_base_url
        ));
    }
    
    public function search_shortcode($atts) {
        $atts = shortcode_atts(array(
            'placeholder' => 'Search XML archives...',
            'button_text' => 'Search'
        ), $atts);
        
        ob_start();
        ?>
        <div class="uri-xml-search-container">
            <form class="uri-xml-search-form" method="get" action="<?php echo home_url('/xml-search-results/'); ?>">
                <div class="search-input-group">
                    <input type="text" 
                           name="q" 
                           class="uri-xml-search-input" 
                           placeholder="<?php echo esc_attr($atts['placeholder']); ?>"
                           value="<?php echo esc_attr(get_query_var('q')); ?>"
                           required>
                    <button type="submit" class="uri-xml-search-button">
                        <?php echo esc_html($atts['button_text']); ?>
                    </button>
                </div>
            </form>
        </div>
        <?php
        return ob_get_clean();
    }
    
    public function ajax_search() {
        check_ajax_referer('uri_xml_search_nonce', 'nonce');
        
        $query = sanitize_text_field($_POST['query']);
        $page = intval($_POST['page']) ?: 1;
        
        if (empty($query)) {
            wp_send_json_error('Query is required');
        }
        
        $api_url = $this->api_base_url . '/search/?q=' . urlencode($query) . '&page=' . $page;
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/json'
            )
        ));
        
        if (is_wp_error($response)) {
            wp_send_json_error('API request failed');
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        wp_send_json_success($data);
    }
    
    public function add_rewrite_rules() {
        add_rewrite_rule('^xml-search-results/?$', 'index.php?xml_search_results=1', 'top');
    }
    
    public function add_query_vars($vars) {
        $vars[] = 'xml_search_results';
        $vars[] = 'q';
        $vars[] = 'page';
        return $vars;
    }
    
    public function template_redirect() {
        if (get_query_var('xml_search_results')) {
            include plugin_dir_path(__FILE__) . 'search-results-template.php';
            exit;
        }
    }
    
    public function admin_menu() {
        add_options_page(
            'URI XML Search Settings',
            'URI XML Search',
            'manage_options',
            'uri-xml-search',
            array($this, 'admin_page')
        );
    }
    
    public function admin_page() {
        if (isset($_POST['submit'])) {
            update_option('uri_xml_search_api_url', sanitize_text_field($_POST['api_url']));
            echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
        }
        
        $api_url = get_option('uri_xml_search_api_url', 'http://127.0.0.1:8000');
        ?>
        <div class="wrap">
            <h1>URI XML Search Settings</h1>
            <form method="post">
                <table class="form-table">
                    <tr>
                        <th scope="row">API Base URL</th>
                        <td>
                            <input type="url" name="api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
                            <p class="description">The base URL of your Django API (e.g., http://127.0.0.1:8000)</p>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }
}

// Initialize the plugin
new URIXMLSearch();

// Activation hook to flush rewrite rules
register_activation_hook(__FILE__, function() {
    flush_rewrite_rules();
});
