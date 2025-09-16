// GrandShopBD Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeSearch();
    initializeTooltips();
    
    // Load vehicle brands for modal
    loadVehicleBrands();
});

// Global variables
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
let selectedBrand = null;
let selectedModel = null;
let selectedYear = null;
let selectedChassis = null;

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    const suggestionsDiv = document.getElementById('searchSuggestions');
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                fetchSearchSuggestions(query);
            }, 300);
        } else {
            if (suggestionsDiv) {
                suggestionsDiv.style.display = 'none';
            }
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (suggestionsDiv && !searchInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    const toast = createToastElement(message, type);
    toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }
    return container;
}

function createToastElement(message, type) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    toast.style.cssText = 'margin-bottom: 10px; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    return toast;
}

// Cart functions (defined globally for template access)
window.addToCart = function(productId, quantity = 1) {
    fetch('/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `product_id=${productId}&quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showToast('Product added to cart!', 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error adding product to cart', 'error');
    });
};

window.buyNow = function(productId, quantity = 1) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/buy-now/';
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    
    const productInput = document.createElement('input');
    productInput.type = 'hidden';
    productInput.name = 'product_id';
    productInput.value = productId;
    
    const quantityInput = document.createElement('input');
    quantityInput.type = 'hidden';
    quantityInput.name = 'quantity';
    quantityInput.value = quantity;
    
    form.appendChild(csrfInput);
    form.appendChild(productInput);
    form.appendChild(quantityInput);
    
    document.body.appendChild(form);
    form.submit();
};

function updateCartCount(count) {
    const cartBadge = document.querySelector('.navbar .badge');
    if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.style.display = count > 0 ? 'inline' : 'none';
    }
}

// Vehicle filter functions
function loadVehicleBrands() {
    // This will be populated from backend or hardcoded for demo
    const brands = [
        {id: 1, name: 'TOYOTA', logo: '/static/images/brands/toyota.png'},
        {id: 2, name: 'HONDA', logo: '/static/images/brands/honda.png'},
        {id: 3, name: 'MITSUBISHI', logo: '/static/images/brands/mitsubishi.png'},
        {id: 4, name: 'NISSAN', logo: '/static/images/brands/nissan.png'},
        {id: 5, name: 'MAZDA', logo: '/static/images/brands/mazda.png'},
        {id: 6, name: 'LEXUS', logo: '/static/images/brands/lexus.png'},
    ];
    
    const brandGrid = document.getElementById('brandGrid');
    if (!brandGrid) return;
    
    let html = '';
    brands.forEach(brand => {
        html += `
            <div class="vehicle-brand-item" onclick="selectBrand(${brand.id}, '${brand.name}')">
                <img src="${brand.logo}" alt="${brand.name}" class="mb-2" style="max-height: 40px;" onerror="this.style.display='none'">
                <div class="fw-medium">${brand.name}</div>
            </div>
        `;
    });
    
    brandGrid.innerHTML = html;
}

console.log('GrandShopBD JavaScript loaded successfully!');