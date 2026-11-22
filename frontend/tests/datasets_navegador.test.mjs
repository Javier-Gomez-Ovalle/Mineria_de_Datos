// Verificación optativa con Chromium instalado, sin nuevas dependencias.
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createServer} from 'node:http';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {dataset_entrenamiento,recursos_dataset} from '../.tests/datos/recursos_datasets.js';

const {chromium}=await import(pathToFileURL(process.env.PLAYWRIGHT_CORE));
const base=process.env.ATO_URL??'http://127.0.0.1:5173/';
const carpeta=new URL('../verificacion_navegador/',import.meta.url);

test('Integración real de Hugging Face', {timeout:240000}, async t=>{
  await mkdir(carpeta,{recursive:true});
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errores=[], solicitudes_principales=[], enlaces_verificados=[];
  page.on('pageerror',e=>errores.push(String(e)));
  page.on('request',r=>{if(r.frame()===page.mainFrame()) solicitudes_principales.push(r.url());});
  try {
    await t.test('Navegación local y visor externo con contenido real',async()=>{
      await page.goto(base);
      await page.locator('a[data_seccion="datasets"]').click();
      assert.equal(await page.locator('#titulo_seccion').innerText(),'Datasets y exploración de datos');
      assert.equal(await page.locator('a[data_seccion="datasets"]').getAttribute('aria-current'),'page');
      await page.locator('.dataset_visor').scrollIntoViewIfNeeded();
      const visor=page.frameLocator('.dataset_visor');
      await visor.getByText('User ID',{exact:true}).first().waitFor({timeout:60000});
      assert.ok(await visor.getByText('User ID',{exact:true}).first().isVisible());
      await page.screenshot({path:fileURLToPath(new URL('datasets_escritorio.png',carpeta)),fullPage:true});
      assert.ok(!solicitudes_principales.some(url=>/dataset_train_fase04\.(csv|parquet)/.test(url)));
    });
    await t.test('Ocho enlaces públicos responden sin descargar el CSV',async()=>{
      const enlaces=await page.locator('.dataset_alternativa a,.dataset_recursos a').evaluateAll(nodos=>nodos.map(n=>({url:n.href,target:n.target,rel:n.rel})));
      assert.equal(enlaces.length,8);
      assert.deepEqual(enlaces.map(e=>e.url),[dataset_entrenamiento.visor,dataset_entrenamiento.csv,...recursos_dataset.map(r=>r.url)]);
      for(const enlace of enlaces) {
        assert.equal(enlace.target,'_blank');assert.match(enlace.rel,/noopener/);
        const respuesta=await page.request.head(enlace.url,{timeout:30000});
        assert.equal(respuesta.status(),200,enlace.url);
        enlaces_verificados.push({url:enlace.url,status:respuesta.status(),metodo:'HEAD'});
      }
    });
    await t.test('Móvil: menú, iframe y página sin desbordamiento horizontal',async()=>{
      await page.setViewportSize({width:390,height:844});
      await page.locator('.boton_menu').click();
      await page.locator('a[data_seccion="datasets"]').click();
      await page.locator('.dataset_visor').scrollIntoViewIfNeeded();
      await page.frameLocator('.dataset_visor').getByText('User ID',{exact:true}).first().waitFor({timeout:60000});
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.equal((await page.locator('.dataset_visor').boundingBox()).height,500);
      await page.screenshot({path:fileURLToPath(new URL('datasets_movil.png',carpeta)),fullPage:true});
    });
    await t.test('Iframe bloqueado: alternativa visible y apertura por teclado',async()=>{
      await page.route('**/embed/viewer/**',route=>route.abort());
      await page.reload();
      const enlace=page.locator('.dataset_alternativa a');
      await enlace.waitFor();await enlace.focus();
      assert.ok(await enlace.isVisible());
      const ventana=page.waitForEvent('popup');await page.keyboard.press('Enter');
      const popup=await ventana;
      await popup.waitForLoadState('domcontentloaded');
      assert.equal(popup.url(),dataset_entrenamiento.visor);
      await popup.close();
    });
    await t.test('Build servido bajo /Mineria_de_Datos/ con catálogo y sección funcionales',async()=>{
      const servidor=createServer(async(req,res)=>{
        try {
          const ruta=new URL(req.url,'http://localhost').pathname;
          if(!ruta.startsWith('/Mineria_de_Datos/')) {res.writeHead(404).end();return;}
          const relativa=ruta.slice('/Mineria_de_Datos/'.length)||'index.html';
          const archivo=new URL(relativa,new URL('../dist/',import.meta.url));
          if(!archivo.href.startsWith(new URL('../dist/',import.meta.url).href)) {res.writeHead(403).end();return;}
          const contenido=await readFile(archivo);
          const extension=relativa.split('.').pop();
          res.setHeader('Content-Type',({html:'text/html',js:'text/javascript',css:'text/css',json:'application/json'})[extension]??'application/octet-stream');
          res.end(contenido);
        } catch {res.writeHead(404).end();}
      });
      await new Promise(resolve=>servidor.listen(0,'127.0.0.1',resolve));
      try {
        await page.goto(`http://127.0.0.1:${servidor.address().port}/Mineria_de_Datos/#datasets`);
        await page.locator('.dataset_visor').waitFor();
        assert.equal(await page.locator('#titulo_seccion').innerText(),'Datasets y exploración de datos');
        assert.equal(await page.locator('#reintentar').count(),0);
        assert.equal(await page.locator('.dataset_visor').getAttribute('src'),dataset_entrenamiento.iframe);
      } finally {await new Promise(resolve=>servidor.close(resolve));}
      assert.deepEqual(errores,[]);
    });
    await writeFile(new URL('datasets_verificacion.json',carpeta),JSON.stringify({enlaces_verificados,errores,descarga_csv_por_aplicacion:false},null,2));
  } finally {await browser.close();}
});
