class DarkModeManager {
  constructor() {
    this.isDarkMode = false;
    this.init();
  }

  init() {
    // Cargar preferencia guardada
    const savedMode = localStorage.getItem('mcscript-dark-mode');
    if (savedMode === 'true') {
      this.enableDarkMode();
    }

    // Crear botón de toggle
    this.createToggleButton();
  }

  createToggleButton() {
    const toggleContainer = document.querySelector('.toggle-container');
    
    // Crear el botón
    const darkModeButton = document.createElement('button');
    darkModeButton.id = 'toggleDarkMode';
    darkModeButton.type = 'button';
    darkModeButton.innerHTML = this.isDarkMode ? '☀️ Modo Claro' : '🌙 Modo Oscuro';
    
    darkModeButton.addEventListener('click', () => {
      this.toggle();
    });

    // Insertar el botón en el contenedor
    toggleContainer.appendChild(darkModeButton);
  }

  toggle() {
    if (this.isDarkMode) {
      this.disableDarkMode();
    } else {
      this.enableDarkMode();
    }
  }

  enableDarkMode() {
    document.body.classList.add('dark-mode');
    this.isDarkMode = true;
    localStorage.setItem('mcscript-dark-mode', 'true');
    this.updateButtonText();

    // Actualizar colores del editor Quill si existe
    this.updateQuillColors();
  }

  disableDarkMode() {
    document.body.classList.remove('dark-mode');
    this.isDarkMode = false;
    localStorage.setItem('mcscript-dark-mode', 'false');
    this.updateButtonText();

    // Restaurar colores del editor Quill
    this.updateQuillColors();
  }

  updateButtonText() {
    const button = document.getElementById('toggleDarkMode');
    if (button) {
      button.innerHTML = this.isDarkMode ? '☀️ Modo Claro' : '🌙 Modo Oscuro';
    }
  }

  updateQuillColors() {
    // Si hay un editor Quill activo, actualizar sus colores según el modo
    const quillEditor = document.querySelector('#editor .ql-editor');
    if (quillEditor && window.quill) {
      if (this.isDarkMode) {
        quillEditor.style.backgroundColor = '#2d2d2d';
        quillEditor.style.color = '#e6e6e6';
        quillEditor.style.borderColor = '#444';
      } else {
        quillEditor.style.backgroundColor = '#F5F5DC';
        quillEditor.style.color = '#2F4F4F';
        quillEditor.style.borderColor = '#8B4513';
      }
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  new DarkModeManager();
});

// Detectar preferencia del sistema
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  // Solo aplicar si no hay preferencia guardada del usuario
  if (!localStorage.getItem('mcscript-dark-mode')) {
    const darkModeManager = window.darkModeManager;
    if (darkModeManager) {
      if (e.matches) {
        darkModeManager.enableDarkMode();
      } else {
        darkModeManager.disableDarkMode();
      }
    }
  }
});