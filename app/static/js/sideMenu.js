function initializeSideMenu() {
    const sideMenuToggle = document.getElementById("sideMenuToggle");
    const sideMenu = document.getElementById("sideMenu");

    if (sideMenuToggle && sideMenu) {
        sideMenuToggle.addEventListener("click", () => {
            sideMenu.classList.toggle("open");
            
            // Update ARIA attributes and button text
            const isOpen = sideMenu.classList.contains("open");
            sideMenuToggle.setAttribute("aria-expanded", isOpen);
            sideMenuToggle.textContent = isOpen ? "Close Menu" : "Saved Results";

            // Add visual feedback
            sideMenuToggle.classList.toggle("active");
        });

        // Add keyboard support
        sideMenu.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                sideMenu.classList.remove("open");
                sideMenuToggle.setAttribute("aria-expanded", "false");
                sideMenuToggle.textContent = "Saved Results";
                sideMenuToggle.classList.remove("active");
                sideMenuToggle.focus();
            }
        });
    } else {
        console.error("Side menu elements not found");
    }
}