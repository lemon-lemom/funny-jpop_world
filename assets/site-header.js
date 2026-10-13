/* 全ページ共通ヘッダー。
   ページ側は <header class="site-header" id="siteHeader" data-page="…"> を置き、その直後でこのファイルを読み込む。
   メニュー項目はここの NAV を直せば全ページに反映される。
   data-bilingual を付けたページだけ言語切替ボタンを出し、ページ側の setLang() / applyLang() と連動する
   (言語は localStorage 'wm_lang' で全ページ共有)。 */
(function(){
  const el = document.getElementById('siteHeader');
  if(!el) return;

  const NAV = [
    {id:'jukebox', href:'jukebox.html',         ico:'🎧', ja:'ジュークボックス', en:'Jukebox'},
    {id:'shindan', href:'shindan.html',         ico:'🔮', ja:'リズム診断',       en:'Rhythm Check'},
    {id:'map',     href:'world-music-map.html', ico:'🗺', ja:'音楽マップ',       en:'Music Map'},
    {id:'gallery', href:'gallery.html',         ico:'📷', ja:'ギャラリー',       en:'Gallery'},
    {id:'pizza',   href:'pizza-time.html',      ico:'🍕', ja:'フリーBGM',        en:'Free BGM'},
    {id:'note',    href:'https://note.com/funny_j_pop', ico:'📝', ja:'note',     en:'note', ext:true},
  ];
  const TXT = {
    sub:  {ja:'▶ チャンネル登録', en:'▶ Subscribe'},
    menu: {ja:'メニュー',         en:'Menu'},
    nav:  {ja:'サイト内メニュー', en:'Site menu'},
  };
  const YT = 'https://www.youtube.com/@FunnyJ-POP?sub_confirmation=1';

  const page = el.dataset.page || '';
  const bilingual = el.hasAttribute('data-bilingual');
  let lang = 'ja';
  if(bilingual){ try{ if(localStorage.getItem('wm_lang') === 'en') lang = 'en'; }catch(e){} }

  el.innerHTML =
    '<a class="sh-logo" href="index.html"><span class="sh-dot"></span>FUNNY J-POP</a>'+
    '<div class="sh-right">'+
      '<nav class="sh-menu" id="shMenu">'+
        NAV.map(n=> '<a class="sh-link" href="'+n.href+'" data-nav="'+n.id+'"'+
          (n.ext ? ' target="_blank" rel="noopener"' : '')+
          (n.id===page ? ' aria-current="page"' : '')+'>'+
          '<span class="sh-ico" aria-hidden="true">'+n.ico+'</span><span class="sh-txt"></span></a>').join('')+
        '<a class="sh-cta" href="'+YT+'" target="_blank" rel="noopener"></a>'+
      '</nav>'+
      (bilingual ? '<button class="sh-lang" type="button" aria-label="Switch language"></button>' : '')+
      '<button class="sh-burger" type="button" aria-controls="shMenu" aria-expanded="false"><span></span><span></span><span></span></button>'+
    '</div>';

  const menu = el.querySelector('.sh-menu');
  const burger = el.querySelector('.sh-burger');
  const langBtn = el.querySelector('.sh-lang');

  function render(){
    NAV.forEach(n=>{ el.querySelector('[data-nav="'+n.id+'"] .sh-txt').textContent = n[lang]; });
    el.querySelector('.sh-cta').textContent = TXT.sub[lang];
    menu.setAttribute('aria-label', TXT.nav[lang]);
    burger.setAttribute('aria-label', TXT.menu[lang]);
    if(langBtn) langBtn.textContent = lang === 'ja' ? 'EN' : '日本語';
  }
  function setOpen(open){
    el.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', String(open));
  }

  burger.addEventListener('click', ()=> setOpen(!el.classList.contains('open')));
  menu.addEventListener('click', e=>{ if(e.target.closest('a')) setOpen(false); });
  document.addEventListener('click', e=>{ if(!el.contains(e.target)) setOpen(false); });
  document.addEventListener('keydown', e=>{ if(e.key === 'Escape') setOpen(false); });

  /* ページ側の applyLang() から呼んでもらい、表示言語をそろえる */
  window.FJHeader = { setLang(l){ lang = l === 'en' ? 'en' : 'ja'; render(); } };

  if(langBtn) langBtn.addEventListener('click', ()=>{
    const next = lang === 'ja' ? 'en' : 'ja';
    if(typeof window.setLang === 'function') window.setLang(next);   // 保存と本文の切替はページ側が行う
    else { try{ localStorage.setItem('wm_lang', next); }catch(e){} }
    window.FJHeader.setLang(next);
  });

  render();
})();
