const toggleBtn = document.getElementById('toggle-btn');
const sidebar = document.getElementById('sidebar');
const mainContent = document.querySelector('.main-content');

toggleBtn.addEventListener('click', () => {
  sidebar.classList.toggle('hidden');
  mainContent.classList.toggle('shifted');
});
