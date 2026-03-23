/* DEVPRINT Portfolio — Client-side filtering and interactions */

document.addEventListener('DOMContentLoaded', () => {
  initFilters();
  initContributionTooltips();
});

function initFilters() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const projectCards = document.querySelectorAll('.project-card');

  if (!filterBtns.length) return;

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Toggle active state
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;

      projectCards.forEach(card => {
        if (filter === 'all') {
          card.style.display = '';
        } else {
          const tags = card.dataset.tags || '';
          const category = card.dataset.category || '';
          const priority = card.dataset.priority || '';

          const matches = tags.includes(filter) ||
                         category === filter ||
                         priority === filter;

          card.style.display = matches ? '' : 'none';
        }
      });
    });
  });
}

function initContributionTooltips() {
  const cells = document.querySelectorAll('.graph-cell[title]');
  cells.forEach(cell => {
    cell.addEventListener('mouseenter', (e) => {
      // Could add floating tooltip here
    });
  });
}

/* Smooth scroll for anchor links */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});
