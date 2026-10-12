/* Offline reader. No network, analytics, account, or demo mutations. */
(()=>{'use strict';
  const $=selector=>document.querySelector(selector);
  const chapters=[...document.querySelectorAll('.chapter')];
  const tasks=[...document.querySelectorAll('[data-task]')];
  const notes=[...document.querySelectorAll('[data-note]')];
  const book=document.body.dataset.book;
  if(!book)return;
  const key='relayworks-free_intro_1-book-'+book+'-1';
  let state={version:1,book,checks:{},notes:{},chapter:chapters[0].id};
  let storageAvailable=true,whole=false;
  const status=(message,error=false)=>{const target=$('#reader-status');target.textContent=message;target.classList.toggle('error',error);};
  const valid=value=>value&&value.version===1&&value.book===book&&typeof value.checks==='object'&&value.checks!==null&&!Array.isArray(value.checks)&&typeof value.notes==='object'&&value.notes!==null&&!Array.isArray(value.notes);
  const sanitize=value=>({version:1,book,checks:Object.fromEntries(tasks.map(t=>[t.dataset.task,value.checks[t.dataset.task]===true])),notes:Object.fromEntries(notes.map(n=>[n.dataset.note,typeof value.notes[n.dataset.note]==='string'?value.notes[n.dataset.note].slice(0,100000):''])),chapter:chapters.some(c=>c.id===value.chapter)?value.chapter:chapters[0].id});
  try{const raw=localStorage.getItem(key);if(raw){const parsed=JSON.parse(raw);if(valid(parsed))state=sanitize(parsed);}}
  catch{storageAvailable=false;status('Browser storage is unavailable. Export progress before closing to keep your checkmarks and notes.',true);}
  function persist(){
    try{localStorage.setItem(key,JSON.stringify(state));storageAvailable=true;}
    catch{storageAvailable=false;status('Progress is held in this tab only. Use Export progress before closing it.',true);}
  }
  function progress(){
    let count=0;
    for(const task of tasks){task.checked=!!state.checks[task.dataset.task];task.closest('li').classList.toggle('done',task.checked);if(task.checked)count++;}
    $('#progress-label').textContent=`${count} of ${tasks.length} complete`;
    $('#progress-bar').style.width=(tasks.length?100*count/tasks.length:0)+'%';
    for(const chapter of chapters){const items=[...chapter.querySelectorAll('[data-task]')];const done=items.filter(t=>t.checked).length;document.querySelector(`[data-chapter-progress="${chapter.id}"]`).textContent=`${done} / ${items.length}`;}
  }
  function printNotes(){for(const note of notes){const text=note.value.trim();const output=document.querySelector(`[data-print-note="${note.dataset.note}"]`);output.textContent=text||'________________________________________________________________________\n\n________________________________________________________________________\n\n________________________________________________________________________';}}
  function restore(){progress();for(const note of notes)note.value=state.notes[note.dataset.note]||'';printNotes();}
  const queryMatches=(chapter,q)=>chapter.textContent.toLocaleLowerCase().includes(q);
  function show(scroll=false){
    const query=$('#book-search').value.trim().toLocaleLowerCase();
    let matches=0;
    for(const chapter of chapters){const match=query?queryMatches(chapter,query):true;chapter.hidden=query?!match:(!whole&&chapter.id!==state.chapter);if(match)matches++;const link=document.querySelector(`[data-chapter-link="${chapter.id}"]`);link.hidden=!!query&&!match;if(chapter.id===state.chapter)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');}
    $('#book-cover').hidden=!!query||(!whole&&state.chapter!==chapters[0].id);
    $('#search-result').hidden=!query;$('#search-result').textContent=`${matches} chapter${matches===1?'':'s'} match “${$('#book-search').value.trim()}”. Clear the search to return to your reading view.`;
    $('#no-results').hidden=!query||matches>0;
    $('.chapter-pager').hidden=whole||!!query;
    const i=chapters.findIndex(c=>c.id===state.chapter);
    $('#previous-button').disabled=i===0;$('#next-button').disabled=i===chapters.length-1;
    $('#chapter-position').textContent=`Chapter ${i+1} of ${chapters.length}`;
    $('#mode-button').textContent=whole?'One chapter at a time':'Read whole book';
    if(scroll)window.scrollTo({top:0,behavior:'instant'});
  }
  function go(id){
    if(!chapters.some(c=>c.id===id))return;
    state.chapter=id;$('#book-search').value='';persist();
    try{history.replaceState(null,'','#'+id);}catch{location.hash=id;}
    show(!whole);
    if(whole)document.getElementById(id).scrollIntoView();
    $('#contents').classList.remove('open');$('#contents-button').setAttribute('aria-expanded','false');
  }
  tasks.forEach(task=>task.addEventListener('change',()=>{state.checks[task.dataset.task]=task.checked;persist();progress();}));
  notes.forEach(note=>note.addEventListener('input',()=>{state.notes[note.dataset.note]=note.value;persist();printNotes();}));
  document.querySelectorAll('[data-chapter-link]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();go(link.dataset.chapterLink);}));
  $('#next-button').addEventListener('click',()=>go(chapters[chapters.findIndex(c=>c.id===state.chapter)+1]?.id));
  $('#previous-button').addEventListener('click',()=>go(chapters[chapters.findIndex(c=>c.id===state.chapter)-1]?.id));
  $('#mode-button').addEventListener('click',()=>{whole=!whole;show(true);});
  $('#book-search').addEventListener('input',()=>show(true));
  $('#contents-button').addEventListener('click',()=>{const open=$('#contents').classList.toggle('open');$('#contents-button').setAttribute('aria-expanded',String(open));});
  $('#print-button').addEventListener('click',()=>{printNotes();window.print();});
  window.addEventListener('beforeprint',printNotes);
  $('#export-button').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({...state,exported_at:new Date().toISOString()},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=`relayworks-${book}-progress-${new Date().toISOString().slice(0,10)}.json`;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);
    status('Progress export prepared. Check your browser downloads and keep the JSON file.');
  });
  $('#import-button').addEventListener('click',()=>$('#import-file').click());
  $('#import-file').addEventListener('change',async event=>{
    const file=event.target.files[0];if(!file)return;
    try{
      if(file.size>5*1024*1024)throw new Error('Choose a progress file smaller than 5 MB.');
      const imported=JSON.parse(await file.text());
      if(!valid(imported))throw new Error('This is not a progress export for this book. Choose the matching Relayworks book JSON.');
      const clean=sanitize(imported);
      // Merge completed checks; imported nonempty notes replace matching local notes.
      for(const [id,checked] of Object.entries(clean.checks))if(checked)state.checks[id]=true;
      for(const [id,note] of Object.entries(clean.notes))if(note)state.notes[id]=note;
      state.chapter=clean.chapter;persist();restore();go(state.chapter);
      status(storageAvailable?'Progress imported. Checkmarks were merged; matching nonempty imported notes replaced local notes.':'Progress imported into this tab. Export before closing because browser storage is unavailable.');
    }catch(error){status('Import failed: '+error.message,true);}finally{event.target.value='';}
  });
  window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(chapters.some(c=>c.id===id)){state.chapter=id;show(true);}});
  const hash=location.hash.slice(1);if(chapters.some(c=>c.id===hash))state.chapter=hash;
  restore();show();
})();
