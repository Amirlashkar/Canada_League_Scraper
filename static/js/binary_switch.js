const checkbox = document.getElementById('btn');
const hiddenLink = document.getElementById('admin_link');

checkbox.addEventListener('click', () => {
  hiddenLink.click();
});
