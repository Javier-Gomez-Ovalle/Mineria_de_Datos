// Verificación externa de recursos agregados publicados; nunca accede a datasets.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(process.env.PLAYWRIGHT_CORE));
const base=process.env.ATO_URL??'https://javier-gomez-ovalle.github.io/Mineria_de_Datos/';

test('Recursos públicos completos y enlaces documentales', {timeout:180000},async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,headless:true});
  try {
    const page=await browser.newPage();
    await page.goto(base); await page.locator('#titulo_seccion').waitFor();
    const fuentes=new Set();
    for(const seccion of ['contexto','metodologia','supervisados','clustering','comparacion','metodos_numericos']) {
      await page.locator(`nav a[data_seccion="${seccion}"]`).click();
      for(const detalle of await page.locator('details').all()) {
        if(await detalle.locator('summary').innerText()!=='Fuentes documentales') continue;
        await detalle.locator('summary').click();
        for(const a of await detalle.locator('a').all()) {
          assert.equal(await a.getAttribute('target'),'_blank');
          assert.match(await a.getAttribute('rel'),/noopener/);
          assert.ok(await a.isVisible());
          fuentes.add(await a.getAttribute('href'));
        }
      }
    }
    assert.equal(fuentes.size,18);
    for(const url of fuentes) {
      const r=await page.request.get(url); assert.equal(r.status(),200,url);
      assert.equal(new URL(r.url()).pathname,new URL(url).pathname);
    }
    await page.goto(new URL('recursos.html',base).href);
    const inventario=JSON.parse(await readFile(new URL('../public/descargas/inventario.json',import.meta.url),'utf8'));
    assert.equal(await page.locator('a[download]').count(),15);
    for(const e of inventario) {
      const enlace=page.locator(`a[href="./descargas/${e.archivo}"]`);
      const descarga=page.waitForEvent('download'); await enlace.click();
      const d=await descarga; const stream=await d.createReadStream(); const partes=[];
      for await(const parte of stream) partes.push(parte);
      const bytes=Buffer.concat(partes);
      assert.equal(bytes.length,e.bytes,e.archivo);
      assert.equal(createHash('sha256').update(bytes).digest('hex'),e.sha256,e.archivo);
    }
    const ppt=await page.request.get(new URL('presentacion/ATO_PRESENTACION_ACADEMICA.pptx',base).href);
    assert.equal(ppt.status(),200);
    assert.deepEqual(await ppt.body(),await readFile(new URL('../public/presentacion/ATO_PRESENTACION_ACADEMICA.pptx',import.meta.url)));
    console.log('18 enlaces documentales; 15 descargas reales con SHA-256; PPTX idéntico.');
  } finally {await browser.close();}
});
