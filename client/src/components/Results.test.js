import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import Results from './Results';
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

test('missing stats stay unverified and reconstructed rows are labeled',async()=>{
 const original=global.fetch;
 global.fetch=jest.fn(async()=>({ok:true,json:async()=>({counts:{},backfilled_count:1,records:[{key:'1',player:'Synthetic Player',direction:'under',line:0.5,stat:'receiving yards',probability:59,first_seen:'2030-01-01T12:00:00Z',backfilled:true,outcome:'unresolved',actual:null,reason:'Missing is not zero.'}],collection:{state:'idle'}})}));
 const container=document.createElement('div');const root=createRoot(container);
 try {
  await act(async()=>root.render(<Results />));
  expect(container.textContent).toContain('Needs review');
  expect(container.textContent).toContain('Actual: not verified');
  expect(container.textContent).toContain('reconstructed later');
  expect(container.textContent).toContain('excluded from prospective counts');
 } finally {act(()=>root.unmount());global.fetch=original;}
});
