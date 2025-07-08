function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

const colorMap = {
  1000: '#ab0ed6', // keyword
  2000: '#e36209', // operator
  3000: '#27c60b', // punctuation
  4000: '#005cc5', // curly-brace
  5000: '#079c29', // bracket
  6000: '#6f42c1', // identifier
  7000: '#005cc5', // integer
  8000: '#005cc5', // float
};

async function updateHighlight() {
  let text = quill.getText(0, quill.getLength() - 1)
                .replace(/\r\n/g, "\n")
                .replace(/^\n+|\n+$/g, "");
  const form = new URLSearchParams();
  form.append('code', text);

  const resp = await fetch('/lex/json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString()
  });
  const {
    tokens,
    lexErrors,
    synErrors,
    semErrorsRows   // <— aquí
  } = await resp.json();

  // 1) Limpio todo el formato previo
  quill.removeFormat(0, text.length);

  // 2) Pinto tokens (color, etc.)...
  tokens.forEach(tok => {
    const color = colorMap[tok.type];
    if (color && tok.length > 0) {
      quill.formatText(tok.index, tok.length, { color });
    }
  });

  // 3) Subrayo errores léxicos y sintácticos
  [...lexErrors, ...synErrors].forEach(err => {
    quill.formatText(err.index, err.length, {
      underline: true,
      color: '#ff0000'
    });
  });

  // 4) Resalto líneas con errores semánticos
  //    Para cada fila row: calculo índice de inicio y longitud de línea
  const lines = text.split('\n');
  semErrorsRows.forEach(row => {
    const lineIdx = row - 1;
    if (lineIdx >= 0 && lineIdx < lines.length) {
      // índice absoluto donde arranca esa línea en el texto
      const start = lines.slice(0, lineIdx).reduce((sum, l) => sum + l.length + 1, 0);
      const length = lines[lineIdx].length;
      quill.formatText(start, length, { background: 'rgba(255,0,0,0.1)' });
    }
  });
}


//Escucha cambios cada 300 ms
quill.on('text-change', debounce(updateHighlight, 300));

document.addEventListener('DOMContentLoaded', updateHighlight);
