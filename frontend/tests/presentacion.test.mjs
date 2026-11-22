import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { secciones, resolver_seccion } from '../.tests/presentacion/secciones.js';
import { crear_estructura, escapar_html, crear_aviso } from '../.tests/componentes/estructura.js';
import { renderizar_contexto, renderizar_seccion, renderizar_error } from '../.tests/presentacion/vistas.js';

const catalogo=JSON.parse(await readFile(new URL('../public/contenido/catalogo.json',import.meta.url),'utf8'));
test('Todas las rutas son únicas y resolubles, incluidas visitas directas',()=>{
  assert.equal(new Set(secciones.map(s=>s.id)).size,6);
  for(const seccion of secciones) assert.equal(resolver_seccion('#'+seccion.id),seccion);
  for(const ruta of ['', '#desconocido','#<script>','#__proto__']) assert.equal(resolver_seccion(ruta).id,'contexto');
});
test('Índice enlaza cada sección y declara controles accesibles',()=>{
  const html=crear_estructura();
  for(const seccion of secciones) assert.ok(html.includes(`data_seccion="${seccion.id}"`));
  assert.match(html,/aria-controls="indice"/);
  assert.match(html,/aria-expanded="false"/);
  assert.match(html,/href="#contenido"/);
  assert.match(html,/rel="noopener noreferrer"/);
});
test('Contenido original se escapa y no se interpreta como HTML',()=>{
  assert.equal(escapar_html('<script>"&\'</script>'),'&lt;script&gt;&quot;&amp;&#39;&lt;/script&gt;');
  const copia=structuredClone(catalogo);
  copia.narrativa.objetivo_general='<img src=x onerror=alert(1)>';
  const html=renderizar_contexto(copia);
  assert.ok(html.includes('&lt;img'));
  assert.ok(!html.includes('<img'));
  assert.ok(crear_aviso('<b>','&').includes('&lt;b&gt;'));
});
test('Contexto conserva objetivos originales y aclara su alcance',()=>{
  const html=renderizar_contexto(catalogo);
  assert.ok(html.includes(escapar_html(catalogo.narrativa.objetivo_general)));
  for(const objetivo of catalogo.narrativa.objetivos_especificos) assert.ok(html.includes(escapar_html(objetivo)));
  assert.match(html,/no garantías de resultados alcanzados/);
  assert.match(html,/<details>/);
});
test('Secciones analíticas preparadas sin gráficas ni métricas inventadas',()=>{
  for(const seccion of secciones.slice(1)){
    const html=renderizar_seccion(seccion);
    assert.match(html,/Contenido analítico pendiente/);
    assert.match(html,/id="titulo_seccion" tabindex="-1"/);
    assert.ok(!/<canvas|<svg|<table/.test(html));
    for(const enlace of html.matchAll(/href="#([^"]+)"/g)) assert.ok(secciones.some(s=>s.id===enlace[1]));
  }
  assert.match(renderizar_seccion(secciones[3],catalogo),/Ward.*Average/);
  assert.match(renderizar_seccion(secciones[4],catalogo),/no un ganador robusto universal/);
});
test('Error ofrece recuperación explícita',()=>{
  assert.match(renderizar_error(),/role="alert"/);
  assert.match(renderizar_error(),/id="reintentar"/);
});
