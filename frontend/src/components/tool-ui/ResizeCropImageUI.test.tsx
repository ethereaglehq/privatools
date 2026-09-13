import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ResizeCropImageUI } from './ResizeCropImageUI';
import { uploadFile, downloadBlob } from '@/lib/api';
vi.mock('@/lib/api',async load=>({...await load<typeof import('@/lib/api')>(),uploadFile:vi.fn(),downloadBlob:vi.fn()}));
vi.mock('@/lib/localStore/defaults',()=>({registerCustomized:vi.fn(),unregisterCustomized:vi.fn()}));
beforeEach(()=>{localStorage.clear();vi.clearAllMocks();vi.mocked(uploadFile).mockResolvedValue(new Response(new Blob(['result'],{type:'image/png'})));});afterEach(cleanup);
describe('image resize output contract',()=>{
 it.each([['weekend.webp','image/webp','weekend_resize.png'],['weekend.jpeg','image/jpeg','weekend_resize.jpg']])('downloads %s using the actual output extension',async(name,type,output)=>{const{container}=render(<ResizeCropImageUI/>);const file=new File(['synthetic image'],name,{type});fireEvent.change(container.querySelector('input[type="file"]')!,{target:{files:[file]}});fireEvent.click(screen.getByRole('button',{name:'Resize to 800×600'}));await waitFor(()=>expect(uploadFile).toHaveBeenCalledWith('/resize-crop-image',file,{width:800,height:600,mode:'resize'},expect.objectContaining({signal:expect.any(AbortSignal)})));await waitFor(()=>expect(downloadBlob).toHaveBeenCalledWith(expect.any(Blob),output));expect(screen.getByText('Actual result')).toBeInTheDocument();});
 it('limits custom dimensions to the server-supported range',()=>{render(<ResizeCropImageUI/>);fireEvent.change(screen.getByRole('spinbutton',{name:'Width (px)'}),{target:{value:'10000'}});expect(screen.getByRole('spinbutton',{name:'Width (px)'})).toHaveValue(8000);fireEvent.change(screen.getByRole('spinbutton',{name:'Height (px)'}),{target:{value:'0'}});expect(screen.getByRole('spinbutton',{name:'Height (px)'})).toHaveValue(1);});
});
