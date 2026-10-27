const schoolInput = document.getElementById('schoolLocation');
const schoolResults = document.getElementById('locationResults');
const schoolHelp = document.getElementById('locationHelp');
let searchTimer;
let searchController;

schoolInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchController?.abort();
    schoolResults.replaceChildren();
    const query = schoolInput.value.trim();
    schoolHelp.textContent = 'Type at least 3 characters for address suggestions, or enter an address manually.';
    if (query.length < 3) return;
    searchTimer = setTimeout(async () => {
        const controller = new AbortController();
        searchController = controller;
        schoolHelp.textContent = 'Searching addresses…';
        try {
            const url = new URL('https://photon.komoot.io/api/');
            url.search = new URLSearchParams({q: query, limit: '5'});
            const response = await fetch(url, {signal: controller.signal});
            if (!response.ok) throw new Error('Address search failed');
            const data = await response.json();
            if (controller.signal.aborted || schoolInput.value.trim() !== query) return;
            for (const feature of data.features || []) {
                const p = feature.properties;
                const address = [...new Set([
                    p.name, [p.housenumber, p.street].filter(Boolean).join(' '),
                    p.city || p.town || p.village, p.state, p.postcode, p.country
                ].filter(Boolean))].join(', ');
                if (!address) continue;
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'list-group-item list-group-item-action';
                button.textContent = address;
                button.addEventListener('click', () => {
                    schoolInput.value = address.slice(0, 500);
                    schoolResults.replaceChildren();
                    schoolHelp.textContent = 'School address selected.';
                    schoolInput.focus();
                });
                schoolResults.append(button);
            }
            schoolHelp.textContent = schoolResults.children.length
                ? 'Select your school address, or enter it manually.'
                : 'No addresses found. Try adding a city, or enter the address manually.';
        } catch (error) {
            if (error.name !== 'AbortError') {
                schoolHelp.textContent = 'Address search is unavailable. Enter your school address manually.';
            }
        }
    }, 400);
});
