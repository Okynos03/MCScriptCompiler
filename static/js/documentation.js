document.addEventListener('DOMContentLoaded', function() {
    // Verificar si es la primera visita
    const hasVisitedBefore = localStorage.getItem('mcscript_visited');
    
    if (!hasVisitedBefore) {
        // Mostrar modal después de un pequeño delay para que la página cargue completamente
        setTimeout(() => {
            showDocumentation();
        }, 1000);
        
        // Marcar que el usuario ya visitó
        localStorage.setItem('mcscript_visited', 'true');
    }
    
    // Agregar event listener al botón de ayuda
    const helpBtn = document.getElementById('helpBtn');
    if (helpBtn) {
        helpBtn.addEventListener('click', showDocumentation);
    }
});

function showDocumentation() {
    const modal = document.getElementById('documentationModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevenir scroll del body
    }
}

function closeDocumentation() {
    const modal = document.getElementById('documentationModal');
    const dontShowAgain = document.getElementById('dontShowAgain');
    
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restaurar scroll del body
    }
    
    // Si el usuario marcó "No mostrar de nuevo", actualizar localStorage
    if (dontShowAgain && dontShowAgain.checked) {
        localStorage.setItem('mcscript_dont_show_docs', 'true');
    }
}

// Cerrar modal al hacer clic fuera del contenido
document.addEventListener('click', function(e) {
    const modal = document.getElementById('documentationModal');
    if (e.target === modal) {
        closeDocumentation();
    }
});

// Cerrar modal con la tecla Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('documentationModal');
        if (modal && modal.style.display === 'block') {
            closeDocumentation();
        }
    }
});