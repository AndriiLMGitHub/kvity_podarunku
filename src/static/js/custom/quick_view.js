document.addEventListener("DOMContentLoaded", function () {
    var quickViewModal = document.getElementById('quick_view_modal');

    if (quickViewModal) {
        quickViewModal.addEventListener('show.bs.modal', function (event) {
            var button = event.relatedTarget;

            // Витягуємо дані (додано description)
            var name = button.getAttribute('data-name');
            var price = button.getAttribute('data-price');
            var oldPrice = button.getAttribute('data-old-price');
            var category = button.getAttribute('data-category');
            var imageSrc = button.getAttribute('data-image');
            var description = button.getAttribute('data-description');
            var badge = button.getAttribute('data-badge');

            // Знаходимо вузли
            var modalTitle = quickViewModal.querySelector('#qv-title');
            var modalPrice = quickViewModal.querySelector('#qv-price');
            var modalOldPrice = quickViewModal.querySelector('#qv-old-price');
            var modalCategory = quickViewModal.querySelector('#qv-categories');
            var modalImage = quickViewModal.querySelector('#qv-image');
            var modalDescription = quickViewModal.querySelector('#qv-description');
            var modalBadge = quickViewModal.querySelector("#qv-badge-container");

            // Підставляємо значення
            if (modalTitle) modalTitle.textContent = name;
            if (modalPrice) modalPrice.textContent = price;

            if (modalImage) {
                modalImage.src = imageSrc;
                modalImage.alt = name;
            }


            if (modalBadge) {
                if (badge && badge !== "None" && badge.trim() !== "") {
                    modalBadge.innerHTML = `<ul><li class="sale-badge">${badge}</li></ul>`;
                    modalBadge.style.display = 'block';
                } else {
                    modalBadge.innerHTML = '';
                    modalBadge.style.display = 'none';
                }
            }

            if (modalCategory && category) {
                modalCategory.innerHTML = '<a href="#">' + category + '</a>';
            }


            if (modalOldPrice) {
                if (oldPrice && oldPrice.trim() !== '') {
                    modalOldPrice.textContent = oldPrice;
                    modalOldPrice.style.display = 'inline-block';
                } else {
                    modalOldPrice.textContent = '';
                    modalOldPrice.style.display = 'none';
                }
            }

            // Підставляємо опис
            if (modalDescription) {
                modalDescription.textContent = description || '';
            }
        });
    }
});