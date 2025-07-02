document.addEventListener('DOMContentLoaded', () => {
  const rightPanel = document.querySelector('.right');
  const toggleBtn   = document.getElementById('toggleAnalysis');
  const textarea    = rightPanel.querySelector('textarea');

  // Función que marca el estado inicial 
  function updateInitialState() {
    if (textarea.value.trim() === '') {
      rightPanel.classList.add('hidden');
      toggleBtn.textContent = 'Mostrar Consola';
    } else {
      rightPanel.classList.remove('hidden');
      toggleBtn.textContent = 'Ocultar Consola';
    }
  }

  // Al hacer clic, alterna visibilidad
  toggleBtn.addEventListener('click', () => {
    const hidden = rightPanel.classList.toggle('hidden');
    toggleBtn.textContent = hidden ? 'Mostrar Consola' : 'Ocultar Consola';
  });

  updateInitialState();
});
