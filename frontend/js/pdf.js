function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
function size(bytes){if(!bytes)return"0 octet";const u=["octets","Ko","Mo","Go"];let n=bytes,i=0;while(n>=1024&&i<3){n/=1024;i++;}return`${n.toFixed(i?1:0)} ${u[i]}`;}
function date(v){const d=new Date(String(v).replace(" ","T")+"Z");return Number.isNaN(d.getTime())?v:d.toLocaleDateString("fr-FR",{day:"2-digit",month:"long",year:"numeric"});}
function cat(v){return String(v||"autres").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-");}
function initials(title){const w=String(title||"Livre").trim().split(/\s+/).filter(Boolean);return(w.length>1?w[0][0]+w[1][0]:w[0].slice(0,2)).toUpperCase();}
const id=new URLSearchParams(location.search).get("id");
(async()=>{
  const loader=document.getElementById("detailLoader"), detail=document.getElementById("detail");
  if(!id){loader.textContent="Livre introuvable.";return;}
  try{
    const res=await fetch(`/api/books/${encodeURIComponent(id)}`), b=await res.json();
    if(!res.ok) throw new Error(b.error||"Livre introuvable.");
    document.title=`${b.title} — DEKAL Books`;
    detail.innerHTML=`
      <article class="detail-card">
        <div class="detail-top">
          <div class="book-cover detail-cover cover-${cat(b.category)}">
            <div class="cover-top"><span>DEKAL</span><span>BOOKS</span></div>
            <div class="cover-main"><small>${esc(b.category)}</small><strong>${esc(b.title)}</strong></div>
            <div class="cover-bottom"><span>${initials(b.title)}</span><span>PDF</span></div>
          </div>
          <div class="detail-info">
            <span class="tag">${esc(b.category)}</span>
            <h1>${esc(b.title)}</h1>
            <p class="meta">Par ${esc(b.author)} · ${date(b.created_at)}</p>
            <p class="detail-description">${esc(b.description)}</p>
            <div class="stats"><span>${size(b.filesize)}</span><span>${b.downloads} téléchargement${b.downloads>1?"s":""}</span></div>
            <div class="card-actions">
              <a class="btn primary" href="/api/books/${b.id}/download">Télécharger le PDF</a>
              <a class="btn secondary" href="/">Retour</a>
            </div>
          </div>
        </div>
        <iframe class="preview" src="/api/books/${b.id}/preview" title="Prévisualisation du PDF"></iframe>
      </article>`;
    detail.hidden=false;
  }catch(e){loader.textContent=e.message;}
  finally{loader.hidden=true;}
})();