/* A4 · glue.js — hidratare imagini (srcset din data-srcset) fara sa blocheze primul ecran.
   Produsul activ are srcset real in HTML. Celelalte 2 heroes: dupa intro (idle) sau la prima atingere.
   Straturile (Ce are?): la prima atingere pe „Ce are?", sau in idle pentru produsul activ (motion.js: warm/ready). */
(function(){
'use strict';
var hero=document.getElementById('hero'); if(!hero) return;
function move(el,from,to){var v=el.getAttribute(from); if(v!==null){el.setAttribute(to,v); el.removeAttribute(from)}}
function hydrate(scope,kind){
  var sel=kind==='layers'?'.prod__layers [data-srcset]':'.prod__visual > picture [data-srcset]';
  var els=scope.querySelectorAll(sel);
  for(var i=0;i<els.length;i++){move(els[i],'data-sizes','sizes');move(els[i],'data-srcset','srcset')}
}
window.SNAQHydrate=function(prodEl,kind){
  if(!prodEl) return;
  if(kind==='all'){hydrate(prodEl,'hero');hydrate(prodEl,'layers')} else hydrate(prodEl,kind);
};
function netOk(){var c=navigator.connection||{}; return !(c.saveData||/(^|-)(2g|3g)$/.test(c.effectiveType||''))}
function allHeroes(){var p=hero.querySelectorAll('.prod');for(var i=0;i<p.length;i++) hydrate(p[i],'hero')}
/* dupa intro: celelalte produse (decodate abia acum), doar daca reteaua permite */
document.addEventListener('snaq:intro-done',function(){
  if(!netOk()) return;
  var idl=window.requestIdleCallback||function(f){return setTimeout(f,500)};
  idl(allHeroes,{timeout:2500});
},{once:true});
/* prima atingere pe tab / stage / sageti: heroes imediat (chiar si pe retea lenta) */
['pointerdown','touchstart','focusin'].forEach(function(ev){
  hero.addEventListener(ev,function(e){
    var t=e.target; if(!t||!t.closest) return;
    if(t.closest('.hero__tab,.hero__stage,.pg')) allHeroes();
    var ex=t.closest('.prod__explode'); if(ex) hydrate(ex.closest('.prod'),'layers');
  },{passive:true,capture:true});
});
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft') allHeroes()},{passive:true});
hero.addEventListener('hero:change',function(e){var d=e.detail||{};var p=hero.querySelectorAll('.prod')[d.to]; if(p) hydrate(p,'hero')});
/* contra-zoom CSS (overrides.css) sincron cu redarea video */
(function(){
  var vs=hero.querySelectorAll('.prod__loop');
  for(var i=0;i<vs.length;i++)(function(v){
    var w=v.parentNode.parentNode;
    v.addEventListener('playing',function(){w.classList.add('is-playing');w.classList.remove('is-paused')});
    v.addEventListener('pause',function(){w.classList.add('is-paused')});
    v.addEventListener('play',function(){w.classList.remove('is-paused')});
  })(vs[i]);
})();

/* nudge: dupa intro, o singura data, burgerul aluneca 12px spre stanga si revine (indiciu ca se poate da swipe). Nu in reduced-motion,
   nu daca omul a atins deja ceva sau a dat scroll. Se opreste la orice interactiune (inainte ca motion.js sa preia .prod__visual). */
(function(){
  var rm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)');
  var tw=null, touched=false;
  function stop(){touched=true; if(tw){tw.kill();tw=null; var v=hero.querySelector('.prod.is-active .prod__visual'); if(v&&window.gsap) gsap.set(v,{clearProps:'x'})}}
  ['pointerdown','touchstart','keydown','wheel'].forEach(function(ev){document.addEventListener(ev,stop,{passive:true,capture:true})});
  document.addEventListener('snaq:intro-done',function(){
    if(touched||(rm&&rm.matches)||!window.gsap||window.scrollY>40) return;
    if(!(window.SNAQHero&&window.SNAQHero.active===0)) return;
    var v=hero.querySelector('.prod.is-active .prod__visual'); if(!v) return;
    setTimeout(function(){
      if(touched||window.scrollY>40||hero.querySelector('.prod.is-exploded')) return;
      tw=gsap.timeline({onComplete:function(){tw=null;gsap.set(v,{clearProps:'x'})}});
      tw.to(v,{x:-12,duration:.3,ease:'power2.out'}).to(v,{x:0,duration:.55,ease:'back.out(2.2)'});
    },450);
  },{once:true});
})();
})();
