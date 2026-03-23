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

          const matches = category === filter ||
                         tags.includes(filter) ||
                         (filter === 'flagship' && parseInt(priority) <= 2);

          card.style.display = matches ? '' : 'none';
        }
      });
    });
  });
}

function initContributionTooltips() {
  const tooltip = document.getElementById('graph-tooltip');
  if (!tooltip) return;

  const cells = document.querySelectorAll('.graph-grid .graph-cell');
  cells.forEach(cell => {
    cell.addEventListener('mouseenter', (e) => {
      const count = parseInt(cell.dataset.count || '0');
      const displayDate = cell.dataset.display || cell.dataset.date;
      const projects = cell.dataset.projects || '';

      // Build tooltip with safe DOM methods
      tooltip.textContent = '';
      const strong = document.createElement('strong');
      strong.textContent = count > 0
        ? count + ' contribution' + (count !== 1 ? 's' : '') + ' on ' + displayDate
        : 'No contributions on ' + displayDate;
      tooltip.appendChild(strong);

      if (projects && count > 0) {
        const projDiv = document.createElement('div');
        projDiv.className = 'tooltip-projects';
        projDiv.textContent = projects;
        tooltip.appendChild(projDiv);
      }

      tooltip.style.display = 'block';

      const rect = cell.getBoundingClientRect();
      tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
      tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
    });

    cell.addEventListener('mouseleave', () => {
      tooltip.style.display = 'none';
    });

    cell.addEventListener('click', () => {
      const projects = cell.dataset.projects;
      if (projects && parseInt(cell.dataset.count) > 0) {
        const firstProject = projects.split(',')[0].trim().toLowerCase()
          .replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
        const projectLink = document.querySelector('a[href*="' + firstProject + '"]');
        if (projectLink) {
          projectLink.click();
        } else {
          window.location.href = '/timeline.html';
        }
      }
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
