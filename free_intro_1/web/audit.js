// Program: free_intro - audit.js
// Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
// Last Modified: 2026-11-18
// Purpose: Script for the rehearsal findings page: switches between its views, plays the screenshot replay, and filters the checklist and exercise lists.

// Everything is wrapped in a function so nothing leaks into the global scope. Frames are the screenshots listed in the report data.
(()=>{'use strict';const $=s=>document.querySelector(s);const $$=s=>[...document.querySelectorAll(s)];let timer=null,index=0;const frames=window.REHEARSAL_FRAMES||[];
/**
 * Show the section named in the address hash (default: results), update the active menu link and stop the replay when leaving it.
 */
function view(){const id=location.hash.slice(1)||'results';const valid=['results','replay','journal','checklist','findings','files'].includes(id)?id:'results';$$('.view').forEach(v=>v.hidden=v.id!==valid);$$('[data-view]').forEach(a=>{if(a.dataset.view===valid)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});if(valid!=='replay')pause();if(valid==='replay')frame(index);}
/**
 * Show screenshot number i (wrapping at both ends) with its title, time, state and counter.
 */
function frame(i){if(!frames.length)return;index=(i+frames.length)%frames.length;const f=frames[index];$('#frame-title').textContent=f.title;$('#frame-meta').textContent=f.time+' · '+f.state;$('#frame-image').src=f.url;$('#frame-image').alt=f.title;$('#frame-link').href=f.url;$('#frame-counter').textContent=(index+1)+' / '+frames.length;$('#frame-slider').value=index;}
/**
 * Stop the automatic replay and reset the button label.
 */
function pause(){clearInterval(timer);timer=null;$('#play-frames').textContent='Play screenshots';}
// Replay controls: previous, next, slider and play/pause (a new frame every 2.8 seconds).
$('#previous-frame').addEventListener('click',()=>{pause();frame(index-1);});$('#next-frame').addEventListener('click',()=>{pause();frame(index+1);});$('#frame-slider').addEventListener('input',e=>{pause();frame(Number(e.target.value));});$('#play-frames').addEventListener('click',()=>{if(timer){pause();return;}$('#play-frames').textContent='Pause';timer=setInterval(()=>frame(index+1),2800);});
/**
 * Show only the checklist items that match the chosen book, status and search text, and update the item count.
 */
function filter(){const book=$('#book-filter').value,status=$('#status-filter').value,query=$('#check-search').value.toLowerCase();let count=0;$$('.check-item').forEach(item=>{item.hidden=!(book==='all'||item.dataset.book===book)||!(status==='all'||item.dataset.status===status)||!item.textContent.toLowerCase().includes(query);if(!item.hidden)count++;});$('#check-count').textContent=count+' items shown';}
// Re-filter as the controls change, filter the exercises by text, and follow address changes.
['book-filter','status-filter','check-search'].forEach(id=>$('#'+id).addEventListener('input',filter));$('#action-search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();$$('.exercise').forEach(item=>item.hidden=!item.textContent.toLowerCase().includes(q));});window.addEventListener('hashchange',view);filter();view();})();
