(() => {
  let user;try{user=localStorage.getItem('p57-user');if(!user){user=Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,'0')).join('');localStorage.setItem('p57-user',user);}}catch{user=Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,'0')).join('');}
  document.getElementById('libraryJoin').onclick=async()=>{
    const status=document.getElementById('libraryStatus'),code=document.getElementById('libraryCode').value.replace(/-/g,'').trim().toUpperCase();
    try{status.textContent='Joining…';const r=await fetch('/api/meetings/'+encodeURIComponent(code),{headers:{'X-P57-User':user}});const m=await r.json();if(!r.ok)throw Error(m.error);if(!m.active)throw Error('This session has ended.');location.href='/api/report/'+m.report+'?meeting='+encodeURIComponent(m.code);}
    catch(e){status.textContent=e.message;}
  };
})();
