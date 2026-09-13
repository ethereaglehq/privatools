import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks=vi.hoisted(()=>({upload:vi.fn(),download:vi.fn()}));
vi.mock('@/lib/api',async original=>({...await original<object>(),uploadFilesWithProgress:mocks.upload,downloadBlob:mocks.download}));
import { MultiFileUI } from './MultiFileUI';
beforeEach(()=>{mocks.upload.mockReset();mocks.download.mockReset();});
function mount(){const view=render(<MultiFileUI endpoint="/audio-merge" accepts=".wav" outputFilename="merged.wav" fileLabel="audio files" actionVerb="Merge"/>);fireEvent.change(view.container.querySelector('input[type=file]')!,{target:{files:[new File(['audio one'],'one.wav'),new File(['audio two'],'two.wav')]}});return view;}
describe('multi-file workspace results',()=>{
 it('retains the completed download and does not upload files again to save another copy',async()=>{
   mocks.upload.mockResolvedValue(new Response(new Blob(['combined']),{headers:{'content-disposition':'attachment; filename="together.wav"'}}));
   mount();fireEvent.click(screen.getByRole('button',{name:'Merge 2 audio files'}));
   await screen.findByRole('button',{name:'Download again'});
   expect(mocks.download).toHaveBeenCalledWith(expect.any(Blob),'one_merged.wav');
   fireEvent.click(screen.getByRole('button',{name:'Download again'}));
   expect(mocks.upload).toHaveBeenCalledTimes(1);expect(mocks.download).toHaveBeenCalledTimes(2);
 });
 it('cancels an in-flight request without claiming a result or losing selected files',async()=>{
   mocks.upload.mockImplementation((_endpoint,_files,_params,_progress,signal:AbortSignal)=>new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')))));
   mount();fireEvent.click(screen.getByRole('button',{name:'Merge 2 audio files'}));
   await act(async()=>{fireEvent.click(screen.getByRole('button',{name:'Cancel'}));});
   await waitFor(()=>expect(screen.getByRole('button',{name:'Merge 2 audio files'})).not.toBeDisabled());
   expect(screen.getByText('one.wav')).toBeVisible();expect(screen.getByText('two.wav')).toBeVisible();expect(mocks.download).not.toHaveBeenCalled();
 });
});
