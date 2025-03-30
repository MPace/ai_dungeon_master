
document.addEventListener('DOMContentLoaded', function() {
    if (typeof marked !== 'undefined') {
        // Configure marked with secure defaults
        marked.setOptions({
            sanitize: true,           // Sanitize HTML
            gfm: true,                // Enable GitHub flavored markdown
            breaks: true,             // Convert line breaks to <br>
            smartLists: true,         // Use smarter list behavior
            smartypants: true         // Use smart punctuation
        });
        console.log('Markdown parser configured');
    }
});