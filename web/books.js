// ==============================================================================
// Program: books.js
// Programmer: Ethan-da-Tech-Wizard
// Last Modified: November 18, 2026
// Purpose: Educational automation and workflow orchestration module for free_intro.
//          Provides structured data generation, asset planning, and contracts.
// ==============================================================================
/* Offline reader. No network, analytics, account, or demo mutations. */
// Reader for the offline checklist books. Persists ticked tasks and notes in localStorage (falling back to
// tab-only memory), supports chapter navigation, whole-book mode, search, print notes, and progress export/import.
(()=>{'use strict';
  // Short query helper and the DOM lists the reader works on.
  const $=selector=>document.querySelector(selector);
  const chapters=[...document.querySelectorAll('.chapter')];
  const tasks=[...document.querySelectorAll('[data-task]')];
  const notes=[...document.querySelectorAll('[data-note]')];
  const book=document.body.dataset.book;
  // Not a book page (e.g. the landing page that also loads this script): do nothing.
  if(!book)return;
  // localStorage key and saved state. The trailing -1 is the storage format revision.
  const key='relayworks-book-'+book+'-1';
  let state={version:1,book,checks:{},notes:{},chapter:chapters[0].id};
  let storageAvailable=true,whole=false;
  // Show a message in the status line (error styles it as a problem).
  const status=(message,error=false)=>{const target=$('#reader-status');target.textContent=message;target.classList.toggle('error',error);};
  // A progress object is valid only for this book, version 1, with plain-object checks and notes.
  const valid=value=>value&&value.version===1&&value.book===book&&typeof value.checks==='object'&&value.checks!==null&&!Array.isArray(value.checks)&&typeof value.notes==='object'&&value.notes!==null&&!Array.isArray(value.notes);
  // Rebuild state from untrusted data: keep only known task/note ids, coerce checks to booleans, cap notes at 100,000 characters and fall back to the first chapter if the saved one is unknown.
  const sanitize=value=>({version:1,book,checks:Object.fromEntries(tasks.map(t=>[t.dataset.task,value.checks[t.dataset.task]===true])),notes:Object.fromEntries(notes.map(n=>[n.dataset.note,typeof value.notes[n.dataset.note]==='string'?value.notes[n.dataset.note].slice(0,100000):''])),chapter:chapters.some(c=>c.id===value.chapter)?value.chapter:chapters[0].id});
  // Load saved progress; if storage is blocked or the JSON is corrupt, continue in memory and warn the reader.
  try{const raw=localStorage.getItem(key);if(raw){const parsed=JSON.parse(raw);if(valid(parsed))state=sanitize(parsed);}}
  catch{storageAvailable=false;status('Browser storage is unavailable. Export progress before closing to keep your checkmarks and notes.',true);}
  /**
   * Save state to localStorage; on failure keep working in memory and tell the reader to export.
   */
  function persist(){
    try{localStorage.setItem(key,JSON.stringify(state));storageAvailable=true;}
    catch{storageAvailable=false;status('Progress is held in this tab only. Use Export progress before closing it.',true);}
  }
  /**
   * Sync checkboxes with state and update the overall and per-chapter progress counters and bar.
   */
  function progress(){
    let count=0;
    for(const task of tasks){task.checked=!!state.checks[task.dataset.task];task.closest('li').classList.toggle('done',task.checked);if(task.checked)count++;}
    $('#progress-label').textContent=`${count} of ${tasks.length} complete`;
    $('#progress-bar').style.width=(tasks.length?100*count/tasks.length:0)+'%';
    for(const chapter of chapters){const items=[...chapter.querySelectorAll('[data-task]')];const done=items.filter(t=>t.checked).length;document.querySelector(`[data-chapter-progress="${chapter.id}"]`).textContent=`${done} / ${items.length}`;}
  }
  /**
   * Mirror typed notes into the print-only blocks (or ruled blank lines when empty) so printouts include them.
   */
  function printNotes(){for(const note of notes){const text=note.value.trim();const output=document.querySelector(`[data-print-note="${note.dataset.note}"]`);output.textContent=text||'________________________________________________________________________\n\n________________________________________________________________________\n\n________________________________________________________________________';}}
  /**
   * Apply saved state to the page: checks, note text and print notes.
   */
  function restore(){progress();for(const note of notes)note.value=state.notes[note.dataset.note]||'';printNotes();}
  // Case-insensitive substring match against a chapter's whole text.
  const queryMatches=(chapter,q)=>chapter.textContent.toLocaleLowerCase().includes(q);
  /**
   * Update visibility for the current mode: search results, single chapter or whole book, cover, pager and button labels.
   * Pass scroll=true to jump back to the top.
   */
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
  /**
   * Switch to a chapter by id (ignored if unknown): clear search, save, update the URL hash and close the mobile contents drawer.
   */
  function go(id){
    if(!chapters.some(c=>c.id===id))return;
    state.chapter=id;$('#book-search').value='';persist();
    try{history.replaceState(null,'','#'+id);}catch{location.hash=id;}
    show(!whole);
    if(whole)document.getElementById(id).scrollIntoView();
    $('#contents').classList.remove('open');$('#contents-button').setAttribute('aria-expanded','false');
  }
  // Event wiring: checkbox and note changes persist immediately.
  tasks.forEach(task=>task.addEventListener('change',()=>{state.checks[task.dataset.task]=task.checked;persist();progress();}));
  notes.forEach(note=>note.addEventListener('input',()=>{state.notes[note.dataset.note]=note.value;persist();printNotes();}));
  // Contents links, previous/next buttons, whole-book toggle, search box, drawer and print controls.
  document.querySelectorAll('[data-chapter-link]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();go(link.dataset.chapterLink);}));
  $('#next-button').addEventListener('click',()=>go(chapters[chapters.findIndex(c=>c.id===state.chapter)+1]?.id));
  $('#previous-button').addEventListener('click',()=>go(chapters[chapters.findIndex(c=>c.id===state.chapter)-1]?.id));
  $('#mode-button').addEventListener('click',()=>{whole=!whole;show(true);});
  $('#book-search').addEventListener('input',()=>show(true));
  $('#contents-button').addEventListener('click',()=>{const open=$('#contents').classList.toggle('open');$('#contents-button').setAttribute('aria-expanded',String(open));});
  $('#print-button').addEventListener('click',()=>{printNotes();window.print();});
  window.addEventListener('beforeprint',printNotes);
  // Export: download the state plus a timestamp as a JSON backup (object URL is released after 5 s).
  $('#export-button').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({...state,exported_at:new Date().toISOString()},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=`relayworks-${book}-progress-${new Date().toISOString().slice(0,10)}.json`;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);
    status('Progress export prepared. Check your browser downloads and keep the JSON file.');
  });
  $('#import-button').addEventListener('click',()=>$('#import-file').click());
  // Import: validate size (< 5 MB) and book identity, sanitize, then merge into the current state.
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
  // Follow manual hash edits and back/forward navigation.
  window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(chapters.some(c=>c.id===id)){state.chapter=id;show(true);}});
  // Honour a chapter in the initial URL hash, then draw the first view.
  const hash=location.hash.slice(1);if(chapters.some(c=>c.id===hash))state.chapter=hash;
  restore();show();
})();
