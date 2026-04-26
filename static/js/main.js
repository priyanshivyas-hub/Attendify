// Dark/Light Mode Toggle
(function() {
    // Get saved theme or default to light
    const savedTheme = localStorage.getItem('attendify-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Toggle function
    window.toggleTheme = function() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('attendify-theme', next);
    };
    
    // Update notification count
    function updateMsgCount() {
        fetch('/api/unread_count')
            .then(res => res.json())
            .then(data => {
                const badge = document.getElementById('msgCount');
                if (badge) {
                    badge.textContent = data.count || 0;
                    badge.style.display = data.count > 0 ? 'inline' : 'none';
                }
            })
            .catch(() => {});
    }
    
    setInterval(updateMsgCount, 30000);
    updateMsgCount();
    
    // Mobile sidebar toggle
    window.toggleSidebar = function() {
        document.querySelector('.sidebar').classList.toggle('open');
    };
})();