jQuery(document).ready(function($) {
    // Handle search form submission
    $('.uri-xml-search-form').on('submit', function(e) {
        // Let the form submit normally to the results page
        return true;
    });
    
    // If we're on the results page, load the results
    if (window.location.pathname.includes('xml-search-results')) {
        loadSearchResults();
    }
    
    // Handle pagination clicks
    $(document).on('click', '.uri-xml-pagination a', function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        var query = getUrlParameter('q');
        
        if (query) {
            loadSearchResults(query, page);
        }
    });
    
    function loadSearchResults(query = null, page = 1) {
        if (!query) {
            query = getUrlParameter('q');
        }
        
        if (!query) {
            return;
        }
        
        // Show loading message
        $('#uri-xml-search-results').html('<div class="uri-xml-loading">Searching archives...</div>');
        
        $.ajax({
            url: uri_xml_search.ajax_url,
            type: 'POST',
            data: {
                action: 'uri_xml_search',
                query: query,
                page: page,
                nonce: uri_xml_search.nonce
            },
            success: function(response) {
                if (response.success) {
                    displayResults(response.data, query);
                } else {
                    $('#uri-xml-search-results').html('<div class="uri-xml-error">Error: ' + response.data + '</div>');
                }
            },
            error: function() {
                $('#uri-xml-search-results').html('<div class="uri-xml-error">Search request failed. Please try again.</div>');
            }
        });
    }
    
    function displayResults(data, query) {
        var html = '';
        
        if (data.count === 0) {
            html = '<div class="uri-xml-no-results">No results found for "' + escapeHtml(query) + '"</div>';
        } else {
            html += '<div class="uri-xml-results-header">';
            html += '<h2>Search Results for "' + escapeHtml(query) + '"</h2>';
            html += '<p class="uri-xml-results-count">Found ' + data.count + ' result(s)</p>';
            html += '</div>';
            
            html += '<div class="uri-xml-results-list">';
            
            data.results.forEach(function(result) {
                html += '<div class="uri-xml-result-item">';
                html += '<h3 class="uri-xml-result-title">';
                html += '<a href="' + result.url + '" target="_blank">' + escapeHtml(decodeURIComponent(result.filename)) + '</a>';
                html += '</h3>';
                html += '<p class="uri-xml-result-snippet">' + escapeHtml(result.snippet) + '</p>';
                html += '<div class="uri-xml-result-meta">';
                html += '<span class="uri-xml-file-size">Size: ' + formatFileSize(result.file_size) + '</span>';
                if (result.last_modified) {
                    html += '<span class="uri-xml-last-modified">Modified: ' + formatDate(result.last_modified) + '</span>';
                }
                html += '<span class="uri-xml-indexed-at">Indexed: ' + formatDate(result.indexed_at) + '</span>';
                html += '</div>';
                html += '</div>';
            });
            
            html += '</div>';
            
            // Add pagination
            if (data.total_pages > 1) {
                html += '<div class="uri-xml-pagination">';
                
                if (data.has_previous) {
                    html += '<a href="#" data-page="' + (data.page - 1) + '" class="uri-xml-page-link">‹ Previous</a>';
                }
                
                for (var i = 1; i <= data.total_pages; i++) {
                    if (i === data.page) {
                        html += '<span class="uri-xml-page-current">' + i + '</span>';
                    } else {
                        html += '<a href="#" data-page="' + i + '" class="uri-xml-page-link">' + i + '</a>';
                    }
                }
                
                if (data.has_next) {
                    html += '<a href="#" data-page="' + (data.page + 1) + '" class="uri-xml-page-link">Next ›</a>';
                }
                
                html += '</div>';
            }
        }
        
        $('#uri-xml-search-results').html(html);
    }
    
    function getUrlParameter(name) {
        var urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }
    
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function formatDate(dateString) {
        if (!dateString) return '';
        var date = new Date(dateString);
        return date.toLocaleDateString();
    }
});
