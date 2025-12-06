var modalSlider, productSlider;

// Initialize productSlider if static products exist
if (document.querySelectorAll(".product").length > 1) {
    productSlider = tns({
        container: "#product",
        items: 1,
        startIndex: 0,
        navContainer: "#productThumbnails",
        navAsThumbnails: true,
        autoplay: false,
        autoplayTimeout: 1500,
        swipeAngle: false,
        speed: 1500,
        controls: false,
        autoplayButtonOutput: false
    });
}

// Function to initialize modalSlider dynamically
function initModalSlider() {
    var modalContainer = document.querySelector("#productModal");
    var modalNav = document.querySelector("#productModalThumbnails");
    
    if (!modalContainer || modalContainer.children.length === 0) return;

    // Destroy previous instance if exists
    if (modalSlider) {
        try { modalSlider.destroy(); } catch (e) {}
        modalSlider = null;
    }

    modalSlider = tns({
        container: "#productModal",
        items: 1,
        startIndex: 0,
        navContainer: "#productModalThumbnails",
        navAsThumbnails: true,
        autoplay: false,
        autoplayTimeout: 1500,
        swipeAngle: false,
        speed: 1500,
        controls: false,
        autoplayButtonOutput: false,
        loop: false
    });
}
