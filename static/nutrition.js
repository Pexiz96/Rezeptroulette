"use strict";

// Geschätzte Nährwerte für bestehende und neue Rezepte. Die Berechnung nutzt
// ausschließlich die in Rezeptroulette hinterlegten Zutaten und übliche
// Durchschnittswerte. Dadurch erhält jedes Rezept sofort eine einheitliche
// Nährwertanzeige, ohne medizinische oder herstellerspezifische Genauigkeit zu
// suggerieren.
(() => {
  const FOOD = [
    [/olivenöl|rapsöl|sonnenblumenöl|pflanzenöl|\böl\b/, {kcal:884,p:0,c:0,f:100,fi:0,s:0,salt:0}],
    [/butter/, {kcal:717,p:.9,c:.1,f:81.1,fi:0,s:.1,salt:.02}],
    [/margarine/, {kcal:720,p:.2,c:.5,f:80,fi:0,s:.5,salt:.5}],
    [/sahne|schlagsahne/, {kcal:292,p:2.1,c:3.2,f:30,fi:0,s:3.2,salt:.08}],
    [/crème fraîche|creme fraiche/, {kcal:292,p:2.4,c:2.8,f:30,fi:0,s:2.8,salt:.08}],
    [/schmand/, {kcal:240,p:2.5,c:3.5,f:24,fi:0,s:3.5,salt:.1}],
    [/frischkäse/, {kcal:245,p:6,c:4,f:23,fi:0,s:4,salt:.8}],
    [/quark/, {kcal:67,p:12,c:4,f:.3,fi:0,s:4,salt:.1}],
    [/skyr/, {kcal:63,p:11,c:4,f:.2,fi:0,s:4,salt:.1}],
    [/joghurt/, {kcal:63,p:4,c:5,f:3.5,fi:0,s:5,salt:.1}],
    [/milch/, {kcal:47,p:3.4,c:4.9,f:1.5,fi:0,s:4.9,salt:.1}],
    [/mozzarella/, {kcal:253,p:18,c:1,f:19,fi:0,s:1,salt:.5}],
    [/feta|hirtenkäse/, {kcal:265,p:14,c:4,f:21,fi:0,s:4,salt:2.5}],
    [/parmesan/, {kcal:431,p:38,c:4,f:29,fi:0,s:.9,salt:1.6}],
    [/gouda|emmentaler|cheddar|käse/, {kcal:356,p:25,c:2,f:27,fi:0,s:.5,salt:1.8}],
    [/hähnchen|hühnchen|hähnchenbrust|putenbrust|pute/, {kcal:110,p:23,c:0,f:1.5,fi:0,s:0,salt:.15}],
    [/rinderhack|hackfleisch|rindfleisch|gulasch/, {kcal:200,p:20,c:0,f:13,fi:0,s:0,salt:.2}],
    [/schweinefleisch|schnitzel|schinken/, {kcal:180,p:21,c:1,f:10,fi:0,s:.5,salt:1.2}],
    [/speck|bacon/, {kcal:417,p:13,c:1,f:40,fi:0,s:.5,salt:2.5}],
    [/lachs/, {kcal:208,p:20,c:0,f:13,fi:0,s:0,salt:.15}],
    [/thunfisch/, {kcal:132,p:29,c:0,f:1,fi:0,s:0,salt:.9}],
    [/fischfilet|kabeljau|seelachs/, {kcal:90,p:20,c:0,f:1,fi:0,s:0,salt:.2}],
    [/ei(er)?\b|\beier\b/, {kcal:143,p:13,c:.7,f:10,fi:0,s:.7,salt:.35}],
    [/spaghetti|nudeln|pasta|penne|tagliatelle|tortellini|spätzle/, {kcal:350,p:12,c:70,f:2,fi:3,s:2,salt:.02}],
    [/reis/, {kcal:350,p:7,c:78,f:.7,fi:1.4,s:.2,salt:.01}],
    [/couscous/, {kcal:360,p:12,c:72,f:2,fi:5,s:.5,salt:.02}],
    [/bulgur/, {kcal:342,p:12,c:76,f:1.3,fi:18,s:.4,salt:.02}],
    [/haferflocken|oats/, {kcal:372,p:13.5,c:59,f:7,fi:10,s:.8,salt:.02}],
    [/mehl/, {kcal:348,p:10,c:72,f:1,fi:4,s:.5,salt:.01}],
    [/brot|toast|brötchen|baguette/, {kcal:250,p:8,c:48,f:2.5,fi:4,s:3,salt:1.2}],
    [/wrap|tortilla/, {kcal:310,p:8,c:52,f:8,fi:4,s:2,salt:1.3}],
    [/kartoffel/, {kcal:77,p:2,c:15,f:.1,fi:2.1,s:.8,salt:.02}],
    [/süßkartoffel/, {kcal:86,p:1.6,c:20,f:.1,fi:3,s:4.2,salt:.1}],
    [/linsen/, {kcal:330,p:24,c:49,f:1.5,fi:11,s:2,salt:.02}],
    [/kichererbsen/, {kcal:164,p:9,c:27,f:2.6,fi:7.6,s:4.8,salt:.05}],
    [/bohnen/, {kcal:120,p:8,c:20,f:.6,fi:6,s:1,salt:.05}],
    [/mais/, {kcal:90,p:3.2,c:16,f:1.2,fi:2.7,s:3.2,salt:.02}],
    [/tomatenmark/, {kcal:82,p:4.3,c:14,f:.5,fi:4,s:11,salt:.2}],
    [/passierte tomaten|gehackte tomaten|tomate/, {kcal:21,p:1,c:3.5,f:.2,fi:1.2,s:2.6,salt:.02}],
    [/paprika/, {kcal:31,p:1,c:5,f:.3,fi:2.1,s:4.2,salt:.01}],
    [/brokkoli/, {kcal:34,p:2.8,c:4,f:.4,fi:2.6,s:1.7,salt:.03}],
    [/spinat/, {kcal:23,p:2.9,c:1.4,f:.4,fi:2.2,s:.4,salt:.2}],
    [/champignon|pilze|pilz/, {kcal:22,p:3.1,c:2.3,f:.3,fi:1,s:2,salt:.02}],
    [/zucchini/, {kcal:17,p:1.2,c:2.2,f:.3,fi:1.1,s:2.5,salt:.02}],
    [/aubergine/, {kcal:25,p:1,c:6,f:.2,fi:3,s:3.5,salt:.01}],
    [/karotte|möhre/, {kcal:41,p:.9,c:7,f:.2,fi:2.8,s:4.7,salt:.07}],
    [/zwiebel/, {kcal:40,p:1.1,c:9,f:.1,fi:1.7,s:4.2,salt:.01}],
    [/knoblauch/, {kcal:149,p:6.4,c:33,f:.5,fi:2.1,s:1,salt:.04}],
    [/avocado/, {kcal:160,p:2,c:8.5,f:14.7,fi:6.7,s:.7,salt:.02}],
    [/banane/, {kcal:89,p:1.1,c:20,f:.3,fi:2.6,s:12,salt:.01}],
    [/apfel/, {kcal:52,p:.3,c:12,f:.2,fi:2.4,s:10,salt:.01}],
    [/erdbeer|himbeer|blaubeer|beeren/, {kcal:45,p:.8,c:8,f:.4,fi:4,s:6,salt:.01}],
    [/honig/, {kcal:304,p:.3,c:82,f:0,fi:0,s:82,salt:.01}],
    [/zucker/, {kcal:400,p:0,c:100,f:0,fi:0,s:100,salt:0}],
    [/schokolade|kakao/, {kcal:520,p:7,c:50,f:32,fi:7,s:45,salt:.05}],
    [/nuss|mandel|walnuss|haselnuss/, {kcal:620,p:18,c:12,f:55,fi:10,s:4,salt:.01}],
    [/erdnussbutter/, {kcal:588,p:25,c:20,f:50,fi:6,s:9,salt:.6}],
    [/kokosmilch/, {kcal:180,p:2,c:3,f:18,fi:1,s:2,salt:.05}]
  ];

  const PIECE_G = [
    [/ei(er)?\b|\beier\b/, 60], [/banane/, 120], [/apfel/, 150], [/paprika/, 150],
    [/tomate/, 100], [/zucchini/, 200], [/aubergine/, 300], [/zwiebel/, 90],
    [/knoblauch/, 5], [/kartoffel/, 150], [/avocado/, 180], [/wrap|tortilla/, 60],
    [/brötchen/, 60], [/brotscheibe|toast/, 35]
  ];

  function num(s){
    if(!s) return 0;
    s=s.replace(",",".").trim();
    if(/^\d+\/\d+$/.test(s)){const [a,b]=s.split("/").map(Number);return b?a/b:0}
    return Number(s)||0;
  }

  function amountInGrams(line){
    const l=line.toLowerCase().replace(/^✓\s*/,"");
    const m=l.match(/(^|\s)(\d+(?:[.,]\d+)?|\d+\/\d+)\s*(kg|g|mg|l|ml|el|tl|stück|stk\.?|dose|dosen|becher|scheibe|scheiben)?\b/i);
    if(!m) return defaultPiece(l);
    const q=num(m[2]), u=(m[3]||"stück").toLowerCase();
    if(u==="kg") return q*1000;
    if(u==="g") return q;
    if(u==="mg") return q/1000;
    if(u==="l") return q*1000;
    if(u==="ml") return q;
    if(u==="el") return q*15;
    if(u==="tl") return q*5;
    if(u.startsWith("dose")) return q*400;
    if(u==="becher") return q*200;
    if(u.startsWith("scheib")) return q*30;
    return q*defaultPiece(l);
  }

  function defaultPiece(line){
    for(const [rx,g] of PIECE_G) if(rx.test(line)) return g;
    return 100;
  }

  function findFood(line){
    const l=line.toLowerCase();
    for(const [rx,n] of FOOD) if(rx.test(l)) return n;
    return null;
  }

  function fallback(title=""){
    const s=title.toLowerCase();
    if(/dessert|kuchen|pancake|waffel|porridge|bowl|skyr|quark/.test(s)) return {kcal:410,p:18,c:52,f:14,fi:6,s:22,salt:.6};
    if(/salat/.test(s)) return {kcal:390,p:22,c:28,f:20,fi:7,s:8,salt:1.3};
    if(/suppe|eintopf/.test(s)) return {kcal:420,p:23,c:48,f:14,fi:9,s:8,salt:1.8};
    if(/pasta|nudel|spaghetti|lasagne|gnocchi|spätzle/.test(s)) return {kcal:620,p:28,c:72,f:23,fi:7,s:8,salt:1.5};
    if(/hähnchen|pute|rind|hack|schnitzel|lachs|fisch/.test(s)) return {kcal:590,p:40,c:42,f:26,fi:6,s:7,salt:1.5};
    return {kcal:520,p:25,c:55,f:21,fi:7,s:9,salt:1.4};
  }

  function calculate(lines, servings, title){
    const total={kcal:0,p:0,c:0,f:0,fi:0,s:0,salt:0};
    let matched=0;
    for(const line of lines){
      const food=findFood(line);
      if(!food) continue;
      const grams=Math.max(0,amountInGrams(line));
      if(!grams) continue;
      matched++;
      const factor=grams/100;
      for(const k of Object.keys(total)) total[k]+=food[k]*factor;
    }
    const n=Math.max(1,Number(servings)||1);
    if(matched<2 || total.kcal/n<120){
      return {...fallback(title), estimated:true, coverage:matched};
    }
    for(const k of Object.keys(total)) total[k]/=n;
    return {...total, estimated:true, coverage:matched};
  }

  function round(v, digits=0){
    const p=10**digits; return Math.round((Number(v)||0)*p)/p;
  }

  function injectNutrition(){
    const main=document.querySelector("#main");
    const hero=main?.querySelector(".detail-hero");
    if(!hero || main.querySelector("#nutritionPanel")) return;
    const lines=[...main.querySelectorAll(".ingredient-list .ingredient")].map(x=>x.textContent.trim()).filter(Boolean);
    const servings=Number(main.querySelector(".detail-copy select")?.value||1);
    const title=main.querySelector(".detail-copy h1")?.textContent||"";
    if(!lines.length || !title) return;
    const n=calculate(lines,servings,title);
    const de=(document.documentElement.lang||"de").toLowerCase().startsWith("de");
    const panel=document.createElement("section");
    panel.id="nutritionPanel";
    panel.className="panel nutrition-panel";
    panel.style.marginTop="18px";
    panel.innerHTML=`
      <div class="section-head" style="margin-bottom:12px">
        <div>
          <span class="eyebrow">${de?"Nährwerte":"Nutrition"}</span>
          <h2 style="margin-top:6px">${de?"Ca. pro Portion":"Approx. per serving"}</h2>
        </div>
      </div>
      <div class="nutrition-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px">
        <div class="pill" style="justify-content:center;padding:12px">🔥 <strong>${round(n.kcal)} kcal</strong></div>
        <div class="pill" style="justify-content:center;padding:12px">💪 ${round(n.p,1)} g ${de?"Eiweiß":"protein"}</div>
        <div class="pill" style="justify-content:center;padding:12px">🍚 ${round(n.c,1)} g ${de?"Kohlenhydrate":"carbs"}</div>
        <div class="pill" style="justify-content:center;padding:12px">🥑 ${round(n.f,1)} g ${de?"Fett":"fat"}</div>
        <div class="pill" style="justify-content:center;padding:12px">🌾 ${round(n.fi,1)} g ${de?"Ballaststoffe":"fiber"}</div>
        <div class="pill" style="justify-content:center;padding:12px">🍬 ${round(n.s,1)} g ${de?"Zucker":"sugar"}</div>
        <div class="pill" style="justify-content:center;padding:12px">🧂 ${round(n.salt,1)} g ${de?"Salz":"salt"}</div>
      </div>
      <p class="hint" style="margin:12px 0 0">${de?"Geschätzte Durchschnittswerte auf Basis der hinterlegten Zutaten. Je nach Produkt, Marke und Zubereitung können die tatsächlichen Werte abweichen.":"Estimated averages based on the stored ingredients. Actual values can vary by product, brand and preparation."}</p>`;
    hero.insertAdjacentElement("afterend",panel);
  }

  const observer=new MutationObserver(()=>requestAnimationFrame(injectNutrition));
  const start=()=>{
    const main=document.querySelector("#main");
    if(main){observer.observe(main,{childList:true,subtree:true});injectNutrition()}
  };
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",start,{once:true});
  else start();
})();
