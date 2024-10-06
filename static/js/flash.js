document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        fetch('/clear_flash')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const flashMessages = document.getElementById('flash-messages');
                    if (flashMessages) {
                        flashMessages.innerHTML = '';
                    }
                }
            });
    }, 10000);
});
