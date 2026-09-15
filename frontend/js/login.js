const form=document.getElementById("loginForm"), msg=document.getElementById("loginMessage"), submitBtn=form.querySelector("button[type=submit]");
let lockTimer=null;

(async()=>{
  const r=await fetch("/api/admin/me"); const d=await r.json();
  if(d.authenticated) location.href="/admin.html";
})();

function startLockCountdown(seconds){
  clearInterval(lockTimer);
  submitBtn.disabled=true;
  let remaining=seconds;
  const tick=()=>{
    msg.textContent=`Trop de tentatives. Réessayez dans ${remaining}s.`;
    if(remaining<=0){
      clearInterval(lockTimer);
      submitBtn.disabled=false;
      msg.textContent="Vous pouvez réessayer.";
    }
    remaining--;
  };
  tick();
  lockTimer=setInterval(tick,1000);
}

form.addEventListener("submit",async e=>{
  e.preventDefault();
  if(submitBtn.disabled) return;
  msg.textContent="Connexion...";
  try{
    const r=await fetch("/api/admin/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:username.value,password:password.value})});
    let d={};
    try{ d=await r.json(); }
    catch{ throw new Error("Réponse invalide du serveur."); }

    if(r.status===429){
      startLockCountdown(d.retry_after||30);
      return;
    }
    if(!r.ok){
      let m=d.error||"Connexion impossible";
      if(typeof d.remaining_attempts==="number"){
        m+=` (${d.remaining_attempts} tentative(s) restante(s))`;
      }
      throw new Error(m);
    }
    location.href="/admin.html";
  }catch(err){msg.textContent=err.message;}
});
