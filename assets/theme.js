/* Apply the saved color scheme before CSS is painted. */
(()=>{let t='light';try{t=localStorage.getItem('zhinote-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}catch{}document.documentElement.dataset.theme=t==='dark'?'dark':'light'})();
