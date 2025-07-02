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
  3000: '#24292e', // punctuation
  4000: '#005cc5', // curly-brace
  5000: '#079c29', // bracket
  6000: '#6f42c1', // identifier
  7000: '#005cc5', // integer
  8000: '#005cc5', // float
};

async function updateHighlight() {
  let text = quill.getText(0, quill.getLength() - 1);
  // o bien, si quieres barrer todo CR/LF:
  text = text.replace(/\r\n/g, "\n").replace(/^\n+|\n+$/g, ""); 
  //const text = quill.getText();
  const form = new URLSearchParams();
  
  form.append('code', text);
  

  const resp = await fetch('/lex/json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString()
  });
  const { tokens, errors } = await resp.json();

  quill.removeFormat(0, text.length);

  //Pinta cada token
  tokens.forEach(tok => {
    const color = colorMap[tok.type];
    if (color && tok.length > 0) {
      quill.formatText(tok.index, tok.length, { color });
    }
  });

  //Subraya errores
  errors.forEach(err => {
    quill.formatText(err.index, err.length, {
      underline: true,
      color: '#ff0000'
    });
  });

}


//Escucha cambios cada 300 ms
quill.on('text-change', debounce(updateHighlight, 300));

document.addEventListener('DOMContentLoaded', updateHighlight);
