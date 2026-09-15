const categories=["Programmation","Cybersécurité","Business","Éducation","Technologie","Développement web","Autres"];
const form=document.getElementById("bookForm"), table=document.getElementById("adminTable"), msg=document.getElementById("adminMessage");
const editId=document.getElementById("editId"), title=document.getElementById("title"), author=document.getElementById("author");
const category=document.getElementById("category"), description=document.getElementById("description"), file=document.getElementById("file");
category.innerHTML=categories.map(c=>`<option>${c}</option>`).join("");
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function date(v){const d=new Date(v.replace(" ","T")+"Z");return Number.isNaN(d.getTime())?v:d.toLocaleDateString("fr-FR");}
async function auth(){
  const r=await fetch("/api/admin/me"),d=await r.json(); if(!d.authenticated) location.href="/login.html";
}
async function load(){
  const r=await fetch("/api/books?per_page=50&sort=recent"),d=await r.json();
  table.innerHTML=d.items.map(b=>`<tr><td>${esc(b.title)}</td><td>${esc(b.category)}</td><td>${b.downloads}</td><td>${date(b.created_at)}</td><td class="actions"><a class="btn secondary" href="/pdf.html?id=${b.id}">Voir</a><button class="btn secondary" data-edit="${b.id}">Modifier</button><button class="btn danger" data-delete="${b.id}">Supprimer</button></td></tr>`).join("");
  table.querySelectorAll("[data-edit]").forEach(b=>b.onclick=()=>editBook(b.dataset.edit));
  table.querySelectorAll("[data-delete]").forEach(b=>b.onclick=()=>removeBook(b.dataset.delete));
}
async function editBook(id){
  const r=await fetch(`/api/books/${id}`),b=await r.json();
  editId.value=b.id; title.value=b.title; author.value=b.author; category.value=b.category; description.value=b.description;
  file.required=false; document.getElementById("formTitle").textContent="Modifier un PDF";
  document.getElementById("submitBtn").textContent="Enregistrer"; document.getElementById("cancelBtn").hidden=false;
  scrollTo({top:0,behavior:"smooth"});
}
document.getElementById("cancelBtn").onclick=()=>resetForm();
function resetForm(){form.reset();editId.value="";file.required=true;document.getElementById("formTitle").textContent="Publier un PDF";document.getElementById("submitBtn").textContent="Publier le PDF";document.getElementById("cancelBtn").hidden=true;msg.textContent="";category.value=categories[0];}
form.addEventListener("submit",async e=>{
  e.preventDefault();msg.textContent="Envoi en cours...";
  const fd=new FormData();fd.append("title",title.value);fd.append("author",author.value);fd.append("description",description.value);fd.append("category",category.value);
  if(file.files[0])fd.append("file",file.files[0]);
  const id=editId.value; const r=await fetch(id?`/api/books/${id}`:"/api/books",{method:id?"PUT":"POST",body:fd});
  const d=await r.json();
  if(!r.ok){msg.textContent=d.error||"Erreur";return;}
  msg.textContent=id?"PDF modifié.":"PDF publié.";resetForm();await load();
});
async function removeBook(id){
  if(!confirm("Supprimer définitivement ce PDF et son fichier ?"))return;
  const r=await fetch(`/api/books/${id}`,{method:"DELETE"}),d=await r.json();
  if(!r.ok){msg.textContent=d.error||"Erreur";return;} await load();
}
document.getElementById("logoutBtn").onclick=async()=>{await fetch("/api/admin/logout",{method:"POST"});location.href="/login.html";};
auth().then(load);
