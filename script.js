function showModal(id) {
    var modal = document.getElementById(id);
    modal.style.display = "block";
}
function closeModal(id) {
    var modal = document.getElementById(id);
    modal.style.display = "none";
}
window.onclick = function (event) {
    if (event.target.className === "modal") {
        event.target.style.display = "none";
    }
}
document.addEventListener('DOMContentLoaded', function () {
    const viewMoreButtons = document.querySelectorAll('.view-more');

    viewMoreButtons.forEach(button => {
        button.addEventListener('click', function () {
            const experience = this.closest('.experience');
            experience.classList.toggle('active');
            const details = experience.getElementsByTagName('ul')[0];
            if (details.style.display === 'block') {
                details.style.display = 'none';
                button.innerHTML = 'View More <i class="fas fa-chevron-down"></i>';
            } else {
                details.style.display = 'block';
                button.innerHTML = 'View Less <i class="fas fa-chevron-up"></i>';
            }
        });
    });
});
document.addEventListener('keyup', function (e) {
    if (e.key === "Escape") {
        var modals = document.querySelectorAll('.modal');
        modals.forEach(function (modal) {
            modal.style.display = "none";
        });
    }
});
