<?php
/**
 * Plugin Name: URI XML Search Link
 * Description: Simple link to external XML search page
 * Version: 1.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Add shortcode for search link
add_shortcode('xml_search_link', function($atts) {
    $atts = shortcode_atts(array(
        'url' => 'https://your-domain.com/xml-search/',
        'text' => 'Search XML Archives',
        'class' => 'xml-search-link'
    ), $atts);
    
    return '<a href="' . esc_url($atts['url']) . '" class="' . esc_attr($atts['class']) . '" target="_blank">' . esc_html($atts['text']) . '</a>';
});

// Add basic styling
add_action('wp_head', function() {
    echo '<style>
        .xml-search-link {
            display: inline-block;
            padding: 12px 20px;
            background-color: #0073aa;
            color: white !important;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s ease;
        }
        .xml-search-link:hover {
            background-color: #005a87;
        }
    </style>';
});
?>
