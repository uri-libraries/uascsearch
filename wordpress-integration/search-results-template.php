<?php
get_header();
?>

<div class="uri-xml-search-results-page">
    <div class="container">
        <div class="content-area">
            <main class="site-main">
                <div class="uri-xml-search-container">
                    <h1>XML Archives Search</h1>
                    
                    <!-- Search form -->
                    <form class="uri-xml-search-form" method="get" action="<?php echo home_url('/xml-search-results/'); ?>">
                        <div class="search-input-group">
                            <input type="text" 
                                   name="q" 
                                   class="uri-xml-search-input" 
                                   placeholder="Search XML archives..."
                                   value="<?php echo esc_attr(get_query_var('q')); ?>"
                                   required>
                            <button type="submit" class="uri-xml-search-button">Search</button>
                        </div>
                    </form>
                    
                    <!-- Results container -->
                    <div id="uri-xml-search-results">
                        <?php if (get_query_var('q')): ?>
                            <div class="uri-xml-loading">Searching archives...</div>
                        <?php else: ?>
                            <div class="uri-xml-no-results">Enter a search term to search the XML archives.</div>
                        <?php endif; ?>
                    </div>
                </div>
            </main>
        </div>
    </div>
</div>

<style>
/* Additional styles for the results page */
.uri-xml-search-results-page {
    padding: 20px 0;
}

.uri-xml-search-results-page .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.uri-xml-search-results-page h1 {
    text-align: center;
    margin-bottom: 30px;
    color: #333;
}

/* Match the WordPress theme styles */
.uri-xml-search-results-page .content-area {
    width: 100%;
}

.uri-xml-search-results-page .site-main {
    background-color: #fff;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
    .uri-xml-search-results-page .container {
        padding: 0 10px;
    }
    
    .uri-xml-search-results-page .site-main {
        padding: 20px;
    }
}
</style>

<?php
get_footer();
?>
