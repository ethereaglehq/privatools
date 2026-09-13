import { useRef, useState } from 'react';
import { ArrowRight, Check, File, Folder, History, Pin, Plus, Search, ShieldCheck, Star, Workflow, X } from 'lucide-react';
import { useFavorites } from '@/hooks/useFavorites';
import { formatRelativeTime } from '@/hooks/useHistory';
import { formatFileSize } from '@/lib/api';
import { storeFileHandoffs, clearFileHandoffs } from '@/lib/file-handoff';
import { FavoriteButton, ToolIcon } from './ConsumerChrome';
import { catalogue, commonSlugs, fileSuggestions, savedWorkflows, searchTools, toolBySlug, toolHref, workflowHref, type ConsumerTool, type RecentTool } from './catalogue';

function DocumentDiagram() {
  const page = (name: string, checklist = false) => <div className="cp-demo-page">
    <div className="cp-demo-page-top"><i/><span>PDF</span></div><b>{name}</b>
    <div className={'cp-demo-lines' + (checklist ? ' cp-demo-checklist' : '')}>{Array.from({length: checklist ? 5 : 6},(_,index) => <span key={index}>{checklist && <Check size={11}/>}<i/></span>)}</div>
    {!checklist && <div className="cp-demo-table">{Array.from({length:9},(_,index) => <i key={index}/>)}</div>}
  </div>;
  return <figure className="cp-file-diagram" aria-label="Example: combine Notes.pdf and Checklist.pdf into one three-page PDF">
    <div className="cp-demo-sources">{page('Notes.pdf')}{page('Checklist.pdf',true)}</div>
    <ArrowRight className="cp-demo-arrow" size={43} strokeWidth={1.5} aria-hidden="true"/>
    <div className="cp-demo-output"><span className="cp-demo-ready"><Check size={14}/>Ready</span>{page('Combined.pdf')}<div className="cp-demo-output-lines cp-demo-lines cp-demo-checklist">{[0,1,2].map(index => <span key={index}><Check size={11}/><i/></span>)}</div><small>3 pages</small></div>
    <figcaption>Illustrative PDF merge</figcaption>
  </figure>;
}

function ToolRow({tool, favorite=false}: {tool:ConsumerTool;favorite?:boolean}) {
  return <div className="cp-tool-row"><a href={toolHref(tool)}><ToolIcon tool={tool}/><span><b>{tool.name}</b><small>{tool.description}</small></span><ArrowRight className="cp-row-arrow" size={21}/></a>{favorite && <FavoriteButton slug={tool.slug}/>}</div>;
}

export function ConsumerHome({history,onClearHistory,files,onFiles,onBrowse,onAi}: {
  history:RecentTool[];onClearHistory:()=>void;files:File[];onFiles:(files:File[])=>void;onBrowse:(query:string)=>void;onAi:()=>void;
}) {
  const input=useRef<HTMLInputElement>(null);
  const search=useRef<HTMLInputElement>(null);
  const [query,setQuery]=useState('');
  const [filter,setFilter]=useState('all');
  const [sending,setSending]=useState(false);
  const [handoffError,setHandoffError]=useState('');
  const [manage,setManage]=useState(false);
  const {favorites,toggle,reorder,pinToTop}=useFavorites();
  const workflows=savedWorkflows();
  const recent=history.filter(item=>toolBySlug.has(item.s));
  const pinned=favorites.map(slug=>toolBySlug.get(slug)).filter((tool):tool is ConsumerTool=>Boolean(tool));
  const returning=Boolean(pinned.length || recent.length || workflows.length || manage);
  const common=commonSlugs.map(slug=>toolBySlug.get(slug)).filter((tool):tool is ConsumerTool=>Boolean(tool));
  const filtered=(query.trim()?searchTools(query):filter==='all'?common:searchTools('')).filter(tool=>filter==='all'||filter==='pdf'&&tool.kind==='pdf'||filter==='image'&&tool.category==='image'||filter==='code'&&tool.category==='developer');
  const suggestions=fileSuggestions(files);
  const openTool=async(tool:ConsumerTool)=>{
    if(sending || files.length>25)return;
    setSending(true);setHandoffError('');
    try{
      await storeFileHandoffs(files,tool.slug);
      location.hash='#/tool/'+tool.slug;
      onFiles([]);
    }catch{setHandoffError('Those files could not be opened. Your selection is still here; try again.');}
    finally{setSending(false);}
  };
  const clearSelection=()=>{clearFileHandoffs();onFiles([]);setHandoffError('');};
  return <div className={'cp-home cp-container'+(returning?' cp-home-returning':'')}>
    <section className="cp-home-hero" aria-labelledby="cp-home-title">
      <div className="cp-hero-copy">
        <h1 id="cp-home-title">{returning?'Ready for your next task?':<>Less file work.<br/>More done.</>}</h1>
        <p className="cp-home-subtitle">{returning?'Your tools, right where you left them.':'PDFs, images, text. Your everyday tools, all in one place.'}</p>
        <div className="cp-home-entry">
          <form className="cp-home-search" role="search" onSubmit={event=>{event.preventDefault();onBrowse(query);}}><Search size={24} aria-hidden="true"/><input ref={search} type="search" aria-label="Find a tool or task" placeholder="What would you like to do?" value={query} onChange={event=>{setQuery(event.target.value);setFilter('all');}}/></form>
          <button type="button" className="cp-button cp-button-primary cp-choose-files" onClick={()=>input.current?.click()}><Plus size={25}/>Choose files</button>
          <input ref={input} type="file" multiple hidden aria-label="Choose files on this device" onChange={event=>{if(event.target.files?.length)onFiles(Array.from(event.target.files));event.target.value='';}}/>
        </div>
        <div className="cp-entry-notes"><p>Free to use. No account needed.</p><p>Select files on this device, then choose a tool.</p></div>
      </div>
      {!returning&&<DocumentDiagram/>}
    </section>

    {files.length>0&&<section className="cp-selected-files" aria-labelledby="cp-selected-title">
      <div className="cp-section-heading"><div><h2 id="cp-selected-title">Choose what happens next</h2><p>{files.length} file{files.length===1?'':'s'} selected on this device. Nothing uploaded.</p></div><button type="button" className="cp-button cp-button-quiet" onClick={clearSelection}>Clear selection</button></div>
      <ul className="cp-selected-list">{files.map((file,index)=><li key={file.name+'-'+index}><File size={19}/><span><b>{file.name}</b><small>{formatFileSize(file.size)}</small></span><button type="button" className="cp-icon-button" aria-label={'Remove '+file.name} onClick={()=>onFiles(files.filter((_,i)=>i!==index))}><X size={18}/></button></li>)}</ul>
      {files.length>25&&<p className="cp-form-error" role="alert">Choose up to 25 files for one handoff. Remove files above or use Batch processing.</p>}
      {suggestions.length?<><p className="cp-selection-help">These tools accept your selection. Review the settings and processing location before starting.</p><div className="cp-suggestions">{suggestions.map(tool=><button className="cp-suggestion cp-button" key={tool.slug} disabled={sending||files.length>25} onClick={()=>void openTool(tool)}><ToolIcon tool={tool} size={25}/><span>{tool.name}</span><ArrowRight size={19}/></button>)}</div></>
        :<div className="cp-empty"><p>These file types need a different tool or separate selections. Your files are still here.</p><a href="/tools" className="cp-text-link">Browse every tool<ArrowRight size={18}/></a></div>}
      {handoffError&&<p className="cp-form-error" role="alert">{handoffError}</p>}
    </section>}

    {returning&&<section className="cp-shortcuts" aria-labelledby="cp-shortcuts-title">
      <div className="cp-section-heading"><h2 id="cp-shortcuts-title">Your shortcuts</h2><button type="button" className="cp-text-button" onClick={()=>setManage(!manage)}>{manage?'Done':'Manage favorites'}</button></div>
      {pinned.length?<div className="cp-shortcut-grid">{pinned.map((tool,index)=><div className="cp-shortcut" key={tool.slug}><ToolRow tool={tool} favorite/>{manage&&<div className="cp-favorite-controls"><button type="button" disabled={index===0} onClick={()=>reorder(favorites.indexOf(tool.slug),favorites.indexOf(pinned[index-1].slug))}>Move left</button><button type="button" disabled={index===pinned.length-1} onClick={()=>reorder(favorites.indexOf(tool.slug),favorites.indexOf(pinned[index+1].slug))}>Move right</button><button type="button" disabled={index===0} onClick={()=>pinToTop(tool.slug)}>Move to start</button></div>}</div>)}</div>
        :<div className="cp-empty cp-empty-inline"><Star size={25}/><p>Pin tools you use often to keep them here.</p><button className="cp-text-button" onClick={()=>setManage(!manage)}>Choose favorites</button></div>}
      {manage&&<div className="cp-pin-picker"><label htmlFor="cp-pin-filter">Find tools to pin</label><input id="cp-pin-filter" className="cp-input" placeholder="Search tools" value={query} onChange={event=>setQuery(event.target.value)}/><div className="cp-pin-options">{searchTools(query).slice(0,20).map(tool=><button type="button" key={tool.slug} className={'cp-pin-option'+(favorites.includes(tool.slug)?' is-on':'')} onClick={()=>toggle(tool.slug)} aria-pressed={favorites.includes(tool.slug)}><ToolIcon tool={tool} size={21}/>{tool.name}<Star size={17} fill={favorites.includes(tool.slug)?'currentColor':'none'}/></button>)}</div></div>}
    </section>}

    <div className="cp-home-workspace">
      <section className="cp-common" aria-labelledby="cp-common-title">
        <div className="cp-section-heading"><h2 id="cp-common-title">{query.trim()?'Search results':'Common tools'}</h2><a href="/tools" className="cp-text-link">All tools<ArrowRight size={21}/></a></div>
        {!returning&&<div className="cp-home-filters" aria-label="Tool categories">{[['all','All'],['pdf','PDF'],['image','Images'],['code','Text & code']].map(([value,label])=><button type="button" className={'cp-filter'+(filter===value?' is-on':'')} key={value} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{label}</button>)}</div>}
        <div className="cp-common-grid">{filtered.slice(0,query.trim()?12:6).map(tool=><ToolRow key={tool.slug} tool={tool}/>)}</div>
        {!filtered.length&&<div className="cp-empty" role="status"><p>No tools match “{query}”. Try a file type or a shorter task name.</p><button type="button" className="cp-text-button" onClick={()=>{setQuery('');setFilter('all');search.current?.focus();}}>Clear search</button></div>}
        {(returning||query.trim())&&<button type="button" className="cp-text-button cp-browse-all" onClick={()=>onBrowse(query)}>Browse {query.trim()?filtered.length+' matching': 'all '+catalogue.length} tools<ArrowRight size={19}/></button>}
      </section>
      {returning&&<aside className="cp-personal-panels">
        <section className="cp-recent" aria-labelledby="cp-recent-title"><div className="cp-section-heading"><h2 id="cp-recent-title">Recently opened</h2><button type="button" className="cp-text-button" onClick={onClearHistory} disabled={!recent.length}>Clear</button></div><p className="cp-panel-note">Tool visits on this device</p>
          {recent.slice(0,4).map(item=>{const tool=toolBySlug.get(item.s)!;return <a className="cp-history-row" href={toolHref(tool)} key={item.s}><History size={28}/><span><b>{tool.name}</b><small>{formatRelativeTime(item.ts)}</small></span><ArrowRight size={21}/></a>;})}
          {!recent.length&&<p className="cp-empty">Tools you open will appear here. File names and contents are never saved in this list.</p>}
        </section>
        <section className="cp-workflows" aria-labelledby="cp-workflows-title"><div className="cp-section-heading"><h2 id="cp-workflows-title">Workflows</h2><a href="/pipeline" className="cp-text-link">View all</a></div>
          {workflows.length?workflows.slice(0,3).map((workflow,index)=><a className="cp-history-row" href={workflowHref(workflow)} key={workflow.name+index}><Workflow size={30}/><span><b>{workflow.name}</b><small>{workflow.slugs.length} steps · choose files to run</small></span><ArrowRight size={20}/></a>):<a className="cp-history-row" href="/pipeline"><Workflow size={30}/><span><b>Create a workflow</b><small>Save a sequence you use again</small></span><ArrowRight size={20}/></a>}
        </section>
      </aside>}
    </div>

    {!returning?<section className="cp-make-yours"><div className="cp-pin-art"><Pin size={34}/></div><div><h2>Make it your space</h2><p>Keep favorite tools and reusable workflows close.</p></div><div className="cp-personal-actions"><button type="button" className="cp-button cp-button-outline" onClick={()=>setManage(true)}><Pin size={20}/>Pin a tool</button><a href="/pipeline" className="cp-text-link">Explore workflows<ArrowRight size={20}/></a></div></section>
      :<div className="cp-local-note"><Pin size={23}/><p><b>Favorites stay close.</b> Your shortcuts and recent tools are remembered on this device.</p></div>}

    <section className="cp-more-possibilities" aria-labelledby="cp-more-title"><div><h2 id="cp-more-title">A little more when you need it.</h2><p>Every tool is free to use. Explore the features that make repeat work easier.</p></div><div className="cp-capability-links"><a href="/batch"><LayersIcon/>Batch processing<ArrowRight size={17}/></a><a href="/my-stuff/vault"><ShieldCheck size={21}/>Password vault<ArrowRight size={17}/></a><button type="button" onClick={onAi}><Plus size={21}/>AI settings<ArrowRight size={17}/></button><a href="/account/keys"><Folder size={21}/>Developer API<ArrowRight size={17}/></a></div></section>
  </div>;
}
function LayersIcon(){return <Workflow size={21}/>;}
