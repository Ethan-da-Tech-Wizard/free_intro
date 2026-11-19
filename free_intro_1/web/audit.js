// ==============================================================================
// Program: audit.js
// Programmer: Ethan-da-Tech-Wizard
// Last Modified: November 18, 2026
// Purpose: Educational automation and workflow orchestration module for free_intro.
//          Provides structured data generation, asset planning, and contracts.
// ==============================================================================
// Behaviour for the rehearsal audit page (AUDIT.html): hash-routed tabs, a screenshot replay player,
// and filters for the checklist and exercise lists. Frame data comes from window.REHEARSAL_FRAMES.
// State: timer = autoplay interval handle, index = current frame, frames = list of {title,time,state,url}.
(()=>{'use strict';const $=s=>document.querySelector(s);const $$=s=>[...document.querySelectorAll(s)];let timer=null,index=0;const frames=window.REHEARSAL_FRAMES||[];
/**
 * Show the section named by the URL hash (default 'results'; unknown names fall back to it), mark its nav link current,
 * stop autoplay when leaving the replay tab and draw the current frame when entering it.
 */
function view(){const id=location.hash.slice(1)||'results';const valid=['results','replay','journal','checklist','findings','files'].includes(id)?id:'results';$$('.view').forEach(v=>v.hidden=v.id!==valid);$$('[data-view]').forEach(a=>{if(a.dataset.view===valid)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});if(valid!=='replay')pause();if(valid==='replay')frame(index);}
/**
 * Display frame i, wrapping around at both ends, and update its title, meta line, image, link, counter and slider.
 */
function frame(i){if(!frames.length)return;index=(i+frames.length)%frames.length;const f=frames[index];$('#frame-title').textContent=f.title;$('#frame-meta').textContent=f.time+' · '+f.state;$('#frame-image').src=f.url;$('#frame-image').alt=f.title;$('#frame-link').href=f.url;$('#frame-counter').textContent=(index+1)+' / '+frames.length;$('#frame-slider').value=index;}
/**
 * Stop autoplay and reset the play button label.
 */
function pause(){clearInterval(timer);timer=null;$('#play-frames').textContent='Play screenshots';}
// Replay controls: previous/next/slider pause autoplay; play toggles a 2.8 s auto-advance.
$('#previous-frame').addEventListener('click',()=>{pause();frame(index-1);});$('#next-frame').addEventListener('click',()=>{pause();frame(index+1);});$('#frame-slider').addEventListener('input',e=>{pause();frame(Number(e.target.value));});$('#play-frames').addEventListener('click',()=>{if(timer){pause();return;}$('#play-frames').textContent='Pause';timer=setInterval(()=>frame(index+1),2800);});
/**
 * Apply the book, status and text filters to the checklist items and update the shown-items count.
 */
function filter(){const book=$('#book-filter').value,status=$('#status-filter').value,query=$('#check-search').value.toLowerCase();let count=0;$$('.check-item').forEach(item=>{item.hidden=!(book==='all'||item.dataset.book===book)||!(status==='all'||item.dataset.status===status)||!item.textContent.toLowerCase().includes(query);if(!item.hidden)count++;});$('#check-count').textContent=count+' items shown';}
// Wire the filters, the exercise search box and hash navigation, then draw the initial state.
['book-filter','status-filter','check-search'].forEach(id=>$('#'+id).addEventListener('input',filter));$('#action-search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();$$('.exercise').forEach(item=>item.hidden=!item.textContent.toLowerCase().includes(q));});window.addEventListener('hashchange',view);filter();view();})();
