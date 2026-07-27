(function(){
  var reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- reveals en cascada --- */
  var io=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(!en.isIntersecting)return;
      var el=en.target;io.unobserve(el);
      var sibs=[].slice.call(el.parentNode.children).filter(function(c){return c.classList&&c.classList.contains('reveal')});
      var d=reduced?0:Math.min(sibs.indexOf(el),12)*60;
      setTimeout(function(){
        el.classList.add('is-in');
        var fin=function(){el.classList.remove('reveal','is-in');el.removeEventListener('transitionend',fin);};
        el.addEventListener('transitionend',fin);
        setTimeout(fin,1200);
      },d);
    });
  },{rootMargin:'0px 0px -5% 0px',threshold:.05});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});

  if(!reduced){
    /* --- scroll --- */
    var bar=document.querySelector('.progress'),
        nav=document.querySelector('.nav'),
        hero=document.querySelector('.hero__img'),
        lastY=0,tick=false;
    function frame(){
      var y=scrollY,max=document.documentElement.scrollHeight-innerHeight;
      if(bar)bar.style.transform='scaleX('+(max>0?y/max:0)+')';
      if(nav){
        nav.classList.toggle('is-solid',y>50);
        nav.classList.toggle('is-hidden',y>400&&y>lastY);
      }
      if(hero&&y<innerHeight)hero.style.translate='0 '+(y*.25).toFixed(1)+'px';
      lastY=y;tick=false;
    }
    addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(frame)}},{passive:true});
    frame();

    /* --- tilt 3D --- */
    if(matchMedia('(hover:hover) and (pointer:fine)').matches){
      document.querySelectorAll('.card').forEach(function(c){
        var r=null;
        c.addEventListener('pointerenter',function(){r=c.getBoundingClientRect();c.classList.add('is-tilt')});
        c.addEventListener('pointermove',function(ev){
          if(!r)return;
          var x=(ev.clientX-r.left)/r.width-.5,y=(ev.clientY-r.top)/r.height-.5;
          c.style.transform='perspective(1000px) translateY(-8px) rotateX('+(-y*8).toFixed(2)+'deg) rotateY('+(x*10).toFixed(2)+'deg)';
        });
        c.addEventListener('pointerleave',function(){r=null;c.classList.remove('is-tilt');c.style.transform='';});
      });
      document.querySelectorAll('.btn').forEach(function(b){
        b.addEventListener('pointermove',function(ev){
          var r=b.getBoundingClientRect(),x=(ev.clientX-r.left)/r.width-.5,y=(ev.clientY-r.top)/r.height-.5;
          b.style.transform='translate('+(x*8).toFixed(1)+'px,'+(y*5).toFixed(1)+'px)';
        });
        b.addEventListener('pointerleave',function(){b.style.transform='';});
      });
    }
  }

  /* --- Lightbox --- */
  var lb=document.getElementById('lightbox');
  if(lb){
    var lbImg=document.getElementById('lb-img'), lbCap=document.getElementById('lb-cap'), lbClose=document.querySelector('.lightbox__close');
    var openLb=function(src,cap){lbImg.src=src;lbCap.textContent=cap;lb.classList.add('is-active');};
    var closeLb=function(){lb.classList.remove('is-active');};
    lb.addEventListener('click',function(e){if(e.target===lb||e.target===lbClose)closeLb()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')closeLb()});
    
    document.querySelectorAll('.card img, .work__figure img').forEach(function(img){
      img.addEventListener('click',function(e){
        e.preventDefault();
        var card=img.closest('.card');
        var cap=card ? card.querySelector('.card__title').textContent : (document.querySelector('h1') ? document.querySelector('h1').textContent : '');
        openLb(img.src, cap);
      });
    });
  }
})();
