document.addEventListener('DOMContentLoaded', () => {
    const collapsibles = document.querySelectorAll('.collapsible');

    collapsibles.forEach((collapsible) => {
        collapsible.addEventListener('click', () => {
            collapsible.classList.toggle('active');
            const content = collapsible.nextElementSibling;
            content.style.display = content.style.display === 'block' ? 'none' : 'block';
        });
    });
});
