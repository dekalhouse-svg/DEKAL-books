const state = { q:"", category:"Tous", sort:"recent", page:1 };
const grid = document.getElementById("bookGrid");
const loader = document.getElementById("loader");
const empty = document.getElementById("empty");
const pagination = document.getElementById("pagination");
const statusBox = document.getElementById("status");
const countBox = document.getElementById("catalogCount");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}
function formatSize(bytes) {
  if (!bytes) return "0 octet";
  const units=["octets","Ko","Mo","Go"]; let n=bytes,i=0;
  while(n>=1024 && i<units.length-1){n/=1024;i++;}
  return `${n.toFixed(i ? 1 : 0)} ${units[i]}`;
}
function formatDate(value) {
  const d = new Date(String(value).replace(" ","T")+"Z");
  return Number.isNaN(d.getTime()) ? value :
    d.toLocaleDateString("fr-FR",{day:"2-digit",month:"short",year:"numeric"});
}
function categoryClass(category){
  return String(category||"autres").toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g,"")
    .replace(/[^a-z0-9]+/g,"-");
}
function initials(title){
  const words=String(title||"Livre").trim().split(/\s+/).filter(Boolean);
  return (words.length>1 ? words[0][0]+words[1][0] : words[0].slice(0,2)).toUpperCase();
}
function renderBooks(items) {
  grid.innerHTML = items.map(b => `
    <article class="book-card">
      <a class="book-cover cover-${categoryClass(b.category)}" href="/pdf.html?id=${b.id}" aria-label="Ouvrir ${escapeHtml(b.title)}">
        <div class="cover-top"><span>DEKAL</span><span>BOOKS</span></div>
        <div class="cover-main">
          <small>${escapeHtml(b.category)}</small>
          <strong>${escapeHtml(b.title)}</strong>
        </div>
        <div class="cover-bottom"><span>${initials(b.title)}</span><span>PDF</span></div>
      </a>
      <div class="book-info">
        <span class="book-category">${escapeHtml(b.category)}</span>
        <h3><a href="/pdf.html?id=${b.id}">${escapeHtml(b.title)}</a></h3>
        <p class="author">${escapeHtml(b.author)}</p>
        <div class="book-meta">
          <span>${formatSize(b.filesize)}</span>
          <span>${b.downloads} téléchargement${b.downloads>1?"s":""}</span>
        </div>
      </div>
      <a class="book-open" href="/pdf.html?id=${b.id}">Consulter <span>→</span></a>
    </article>`).join("");
}
function renderPagination(data) {
  pagination.innerHTML="";
  if(data.pages<=1) return;
  const add=(label,page,disabled=false,active=false)=>{
    const b=document.createElement("button");
    b.textContent=label; b.disabled=disabled; b.className=active?"active":"";
    b.onclick=()=>{state.page=page;loadBooks();};
    pagination.appendChild(b);
  };
  add("←",data.page-1,data.page<=1);
  for(let p=1;p<=data.pages;p++){
    if(data.pages>7 && p!==1 && p!==data.pages && Math.abs(p-data.page)>1) continue;
    add(String(p),p,false,p===data.page);
  }
  add("→",data.page+1,data.page>=data.pages);
}
async function loadBooks(){
  loader.hidden=false; empty.hidden=true; grid.innerHTML=""; statusBox.hidden=true;
  const params=new URLSearchParams({
    q:state.q,category:state.category,sort:state.sort,page:state.page,per_page:12
  });
  try{
    const res=await fetch(`/api/books?${params}`);
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||"Impossible de charger la bibliothèque.");
    renderBooks(data.items);
    renderPagination(data);
    empty.hidden=data.items.length!==0;
    countBox.textContent = `${data.total} ressource${data.total>1?"s":""}`;
  }catch(e){
    statusBox.textContent=e.message; statusBox.hidden=false;
  }finally{loader.hidden=true;}
}
document.getElementById("searchInput").addEventListener("input",e=>{
  state.q=e.target.value.trim(); state.page=1; loadBooks();
});
document.querySelectorAll(".filter").forEach(btn=>btn.addEventListener("click",()=>{
  document.querySelectorAll(".filter").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active"); state.category=btn.dataset.category; state.page=1; loadBooks();
}));
document.getElementById("sortSelect").addEventListener("change",e=>{
  state.sort=e.target.value; state.page=1; loadBooks();
});
document.getElementById("year").textContent=new Date().getFullYear();
loadBooks();
