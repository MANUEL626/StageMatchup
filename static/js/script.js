const locationInput = document.getElementById('locality');
const datalist = document.getElementById('suggestions');

locationInput.addEventListener('input', function() {
    const query = this.value;
    fetch(`/suggestion?query=${query}`)
        .then(response => response.json())
        .then(suggestions => {
            datalist.innerHTML = '';
            suggestions.forEach(locality => {
                const option = document.createElement('option');
                option.value = locality;
                datalist.appendChild(option);
            });
        });
});
