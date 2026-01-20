document.addEventListener('DOMContentLoaded', function() {
    const navbarToggle = document.getElementById('navbarToggle');
    const navLinks = document.getElementById('navLinks');

    if (navbarToggle && navLinks) {
        let lastTap = 0;

        function toggleMenu() {
            navbarToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
        }

        navbarToggle.addEventListener('touchend', function(e) {
            e.preventDefault();
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;

            if (tapLength < 500 && tapLength > 0) {
                return;
            }

            lastTap = currentTime;
            toggleMenu();
        }, { passive: false });

        navbarToggle.addEventListener('click', function(e) {
            const currentTime = new Date().getTime();
            const timeSinceTouch = currentTime - lastTap;

            if (timeSinceTouch > 500 || timeSinceTouch === currentTime) {
                e.preventDefault();
                toggleMenu();
            }
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    navbarToggle.classList.remove('active');
                    navLinks.classList.remove('active');
                }
            });
        });

        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 &&
                !navbarToggle.contains(e.target) &&
                !navLinks.contains(e.target) &&
                navLinks.classList.contains('active')) {
                navbarToggle.classList.remove('active');
                navLinks.classList.remove('active');
            }
        });
    }
});
