// Prueba en Chromium real aislado. No usa Edge, datasets ni servicios externos.
// PLAYWRIGHT_CORE: ruta al index.mjs de playwright-core ya instalado.
// CHROMIUM_PATH: ejecutable de Chromium ya instalado.
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
const {chromium}=await import(pathToFileURL(process.env.PLAYWRIGHT_CORE));
const base=process.env.ATO_URL??'http://127.0.0.1:5173/';
const carpeta=new URL('../verificacion_navegador/',import.meta.url);
const catalogo=JSON.parse(await readFile(new URL('../public/contenido/catalogo.json',import.meta.url),'utf8'));

test('Inicialización y navegación real en Chromium', {timeout:90000}, async t=>{
  await mkdir(carpeta,{recursive:true});
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errores=[],solicitudes=[],respuestas=[];
  page.on('pageerror',error=>errores.push(String(error)));
  page.on('request',r=>solicitudes.push(r.url()));
  page.on('response',r=>respuestas.push({url:r.url(),status:r.status()}));
  try {
    await t.test('fetch nativo solicita y valida el catálogo durante el arranque',async()=>{
      const respuesta=page.waitForResponse(r=>r.url().endsWith('/contenido/catalogo.json'));
      await page.goto(base);
      const r=await respuesta;
      assert.equal(r.status(),200);assert.deepEqual(await r.json(),catalogo);
      await page.locator('#titulo_seccion').waitFor();
      assert.match(await page.locator('main').innerText(),/Una credencial válida/);
      assert.equal(await page.locator('#reintentar').count(),0);
    });
    await t.test('Las seis secciones presentan contenido y generan capturas',async()=>{
      for(const [id,texto] of [['contexto','La pregunta se convierte'],['metodologia','Fuentes y alcance'],['supervisados','OOF global'],['clustering','Candidatos históricos'],['comparacion','Evaluación final documentada'],['metodos_numericos','Interpolación de Lagrange']]) {
        await page.locator(`nav a[data_seccion="${id}"]`).click();
        await page.waitForFunction(texto=>document.querySelector('main')?.textContent.includes(texto),texto);
        assert.equal(await page.locator('main #reintentar').count(),0);
        assert.equal(await page.locator(`nav a[data_seccion="${id}"]`).getAttribute('aria-current'),'page');
        await page.screenshot({path:fileURLToPath(new URL(id+'_escritorio.png',carpeta)),fullPage:false});
      }
    });
    await t.test('Controles reales filtran protocolo, modelo, ámbito y fold',async()=>{
      await page.locator('nav a[data_seccion="supervisados"]').click();
      await page.locator('#filtro_protocolo').selectOption('anidada');
      await page.locator('#filtro_modelo').selectOption('arbol_ponderado');
      await page.locator('#filtro_ambito').selectOption('fold');
      await page.locator('#filtro_fold').selectOption('3');
      const filas=page.locator('.tabla_desplazable').first().locator('tbody tr');
      assert.equal(await filas.count(),1);
      const fuente=catalogo.resultados.find(r=>r.protocolo==='anidada'&&r.ambito==='fold'&&r.valores.modelo==='arbol_ponderado'&&r.valores.regla==='aprendido'&&r.valores.fold_externo===3);
      assert.equal(await filas.locator('td').nth(1).getAttribute('title'),String(fuente.valores.tp));
    });
    await t.test('Las 58 figuras se decodifican; visor abre y cierra',async()=>{
      const imagenes=await page.evaluate(async figuras=>Promise.all(figuras.map(f=>new Promise(resolve=>{
        const img=new Image();img.onload=()=>resolve({id:f.id,ok:img.naturalWidth===f.ancho&&img.naturalHeight===f.alto});img.onerror=()=>resolve({id:f.id,ok:false});img.src='./'+f.url;
      }))),catalogo.figuras);
      assert.equal(imagenes.length,58);assert.ok(imagenes.every(i=>i.ok),JSON.stringify(imagenes.filter(i=>!i.ok)));
      await page.locator('.ampliar_figura').first().click();
      assert.equal(await page.locator('dialog').evaluate(d=>d.open),true);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('dialog').evaluate(d=>d.open),false);
    });
    await t.test('Móvil: menú, navegación y ausencia de desbordamiento global',async()=>{
      await page.setViewportSize({width:390,height:844});
      await page.locator('.boton_menu').click();
      assert.equal(await page.locator('.boton_menu').getAttribute('aria-expanded'),'true');
      await page.locator('nav a[data_seccion="contexto"]').click();
      assert.equal(await page.locator('.boton_menu').getAttribute('aria-expanded'),'false');
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await page.screenshot({path:fileURLToPath(new URL('contexto_movil.png',carpeta)),fullPage:true});
    });
    await t.test('Errores de fuente y reintento en navegador real',async()=>{
      await page.route('**/contenido/catalogo.json',route=>route.fulfill({status:503,body:'No disponible'}));
      await page.reload();await page.locator('#reintentar').waitFor();
      assert.equal(await page.locator('[role="alert"]').count(),1);
      await page.unroute('**/contenido/catalogo.json');
      await page.locator('#reintentar').click();
      await page.waitForFunction(()=>document.querySelector('main')?.textContent.includes('Una credencial válida'));
      assert.equal(await page.locator('#reintentar').count(),0);
    });
    await t.test('Sin excepciones JavaScript no gestionadas',()=>assert.deepEqual(errores,[]));
    await writeFile(new URL('ejecucion.json',carpeta),JSON.stringify({url:base,navegador:await browser.version(),errores,solicitudes,respuestas,nota:'El 503 del catálogo se induce deliberadamente para verificar recuperación.'},null,2));
  } finally {await browser.close();}
});
