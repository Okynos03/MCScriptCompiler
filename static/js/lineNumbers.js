document.addEventListener('DOMContentLoaded', () => {
  const quill = window.quill || Quill.find(document.querySelector('#editor'));
  const gutter = document.querySelector('.line-numbers');
  const editorEl = document.querySelector('.ql-editor');

  // 2) Sincronizar scroll entre editor y gutter
  editorEl.addEventListener('scroll', () => {
    gutter.scrollTop = editorEl.scrollTop;
  });

  function updateLineNumbers() {
    const text = quill.getText();
    const lineCount = Math.max(1, text.split('\n').length - 1);
    
    let nums = '';
    for (let i = 1; i <= lineCount; i++) {
      nums += i + '\n';
    }
    
    gutter.textContent = nums;
  }

  updateLineNumbers();
  quill.on('text-change', updateLineNumbers);
  quill.on('selection-change', (range) => {
    if (range) {
      updateLineNumbers();
    }
  });
});