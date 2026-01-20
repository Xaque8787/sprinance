console.log('Management System loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    const navbarToggle = document.getElementById('navbarToggle');
    const navLinks = document.getElementById('navLinks');

    console.log('navbarToggle:', navbarToggle);
    console.log('navLinks:', navLinks);

    if (navbarToggle && navLinks) {
        console.log('Adding click listener to hamburger menu');
        navbarToggle.addEventListener('click', function(e) {
            console.log('Hamburger clicked!');
            e.preventDefault();
            navbarToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
            console.log('Toggle classes updated');
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    navbarToggle.classList.remove('active');
                    navLinks.classList.remove('active');
                }
            });
        });
    } else {
        console.error('Could not find navbar elements');
    }
});
