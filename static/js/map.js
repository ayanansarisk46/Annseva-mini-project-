/**
 * AnnSeva - Map Controller (map.js)
 * Dual-Mode Engine:
 * 1. Uses Google Maps JavaScript API if `GOOGLE_MAPS_API_KEY` is set.
 * 2. Seamlessly falls back to Leaflet.js (OpenStreetMap) if key is empty or invalid.
 * Renders interactive markers for Donors, Active Donations, and registered NGOs.
 */

document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Fetch marker locations from API
    fetch('/api/map-data')
        .then(response => response.json())
        .then(data => {
            renderMap(data);
        })
        .catch(err => {
            console.error('Failed to load map data:', err);
        });
});

function renderMap(data) {
    const donations = data.donations || [];
    const ngos = data.ngos || [];

    // Default center (Mumbai coordinates: 19.0760, 72.8777, or center of first marker)
    let centerLat = 19.0760;
    let centerLng = 72.8777;

    if (donations.length > 0 && donations[0].lat && donations[0].lng) {
        centerLat = donations[0].lat;
        centerLng = donations[0].lng;
    } else if (ngos.length > 0 && ngos[0].lat && ngos[0].lng) {
        centerLat = ngos[0].lat;
        centerLng = ngos[0].lng;
    }

    // Check if Google Maps API is loaded and valid
    if (window.google && window.google.maps) {
        initGoogleMap(centerLat, centerLng, donations, ngos);
    } else {
        initLeafletMap(centerLat, centerLng, donations, ngos);
    }
}

/**
 * 1. Google Maps Renderer
 */
function initGoogleMap(centerLat, centerLng, donations, ngos) {
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 12,
        center: { lat: centerLat, lng: centerLng },
        styles: [
            { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }
        ]
    });

    const infoWindow = new google.maps.InfoWindow();

    // NGO Markers (Green icons)
    ngos.forEach(ngo => {
        if (!ngo.lat || !ngo.lng) return;
        const marker = new google.maps.Marker({
            position: { lat: ngo.lat, lng: ngo.lng },
            map: map,
            title: ngo.name,
            icon: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
        });

        marker.addListener('click', () => {
            infoWindow.setContent(`
                <div style="padding: 8px;">
                    <h4 style="margin: 0 0 5px 0; color: #059669;">${ngo.name}</h4>
                    <p style="margin: 0; font-size: 13px;"><strong>Role:</strong> NGO Center</p>
                    <p style="margin: 0; font-size: 13px;"><strong>Location:</strong> ${ngo.location}</p>
                    <p style="margin: 0; font-size: 13px;"><strong>Contact:</strong> ${ngo.phone}</p>
                </div>
            `);
            infoWindow.open(map, marker);
        });
    });

    // Donation Markers (Orange/Red icons)
    donations.forEach(donation => {
        if (!donation.lat || !donation.lng) return;
        const marker = new google.maps.Marker({
            position: { lat: donation.lat, lng: donation.lng },
            map: map,
            title: donation.title,
            icon: 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png'
        });

        marker.addListener('click', () => {
            infoWindow.setContent(`
                <div style="padding: 8px;">
                    <h4 style="margin: 0 0 5px 0; color: #d97706;">${donation.title}</h4>
                    <p style="margin: 0; font-size: 13px;"><strong>Donor:</strong> ${donation.donor}</p>
                    <p style="margin: 0; font-size: 13px;"><strong>Status:</strong> ${donation.status}</p>
                    <p style="margin: 0; font-size: 13px;"><strong>Pickup:</strong> ${donation.time}</p>
                    <p style="margin: 0; font-size: 13px;"><strong>Address:</strong> ${donation.location}</p>
                    <a href="/donation/${donation.id}" style="display:inline-block; margin-top:6px; color:#059669; font-weight:bold;">View Details &rarr;</a>
                </div>
            `);
            infoWindow.open(map, marker);
        });
    });
}

/**
 * 2. Leaflet (OpenStreetMap) Fallback Renderer
 */
function initLeafletMap(centerLat, centerLng, donations, ngos) {
    if (typeof L === 'undefined') {
        document.getElementById('map').innerHTML = `
            <div style="text-align: center; padding: 40px; color: #64748b;">
                <h3>Map Service Available</h3>
                <p>Configure GOOGLE_MAPS_API_KEY in .env or connect to internet to load tile layers.</p>
            </div>
        `;
        return;
    }

    const map = L.map('map').setView([centerLat, centerLng], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
    }).addTo(map);

    // NGO Markers (Green icon style)
    const ngoIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    // Donation Markers (Orange icon style)
    const foodIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    // Add NGO Markers
    ngos.forEach(ngo => {
        if (!ngo.lat || !ngo.lng) return;
        L.marker([ngo.lat, ngo.lng], { icon: ngoIcon })
            .addTo(map)
            .bindPopup(`
                <div style="font-family: inherit; font-size: 13px;">
                    <strong style="color: #059669; font-size: 14px;">🏢 NGO: ${ngo.name}</strong><br>
                    <strong>Location:</strong> ${ngo.location}<br>
                    <strong>Phone:</strong> ${ngo.phone}
                </div>
            `);
    });

    // Add Donation Markers
    donations.forEach(donation => {
        if (!donation.lat || !donation.lng) return;
        L.marker([donation.lat, donation.lng], { icon: foodIcon })
            .addTo(map)
            .bindPopup(`
                <div style="font-family: inherit; font-size: 13px;">
                    <strong style="color: #d97706; font-size: 14px;">🍲 ${donation.title}</strong><br>
                    <strong>Donor:</strong> ${donation.donor}<br>
                    <strong>Status:</strong> <span style="text-transform:uppercase; font-weight:bold;">${donation.status}</span><br>
                    <strong>Pickup:</strong> ${donation.time}<br>
                    <a href="/donation/${donation.id}" style="color: #059669; font-weight: bold; display: inline-block; margin-top: 5px;">View Details &rarr;</a>
                </div>
            `);
    });
}
