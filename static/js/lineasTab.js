document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    //desactiva todas las pestañas y contenidos
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    //activo lo que se clickie
    btn.classList.add('active');
    document.getElementById(btn.dataset.target).classList.add('active');
  });
});
