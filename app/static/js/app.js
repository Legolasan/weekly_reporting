// Work Tracker - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any global functionality here
    console.log('Work Tracker initialized');
    
    // Form validation for points
    const pointsInputs = document.querySelectorAll('input[name="assigned_points"]');
    pointsInputs.forEach(input => {
        input.addEventListener('input', function() {
            const max = parseInt(this.getAttribute('max')) || 100;
            const value = parseInt(this.value) || 0;
            
            if (value > max) {
                this.classList.add('border-red-500');
                this.setCustomValidity(`Maximum ${max} points allowed`);
            } else {
                this.classList.remove('border-red-500');
                this.setCustomValidity('');
            }
        });
    });

    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
});

// Utility function to format dates
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
    });
}

// Export for use in templates
window.WorkTracker = {
    formatDate
};
