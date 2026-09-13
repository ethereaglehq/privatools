import type { ReactNode, RefObject } from 'react';
import { ArrowLeft, ArrowUp, ArrowUpRight, Check, Copy, History, BookOpen } from 'lucide-react';
import { StudioPage, StudioHeader } from './Studio';
import './documents.css';

type Section = { id: string; title: string };
export function DocumentStudio({ title, description, updated, historyHref, sections, activeId, onSection, progress, articleRef, copied, onCopy, onTop, showTop, children }: {
  title: string; description: string; updated: string; historyHref: string;
  sections: Section[]; activeId: string | null; onSection: (id: string) => void;
  progress: number; articleRef: RefObject<HTMLElement>; copied: boolean;
  onCopy: () => void; onTop: () => void; showTop: boolean; children: ReactNode;
}) {
  return <StudioPage className="pt-document-page">
    <nav className="pt-document-nav" aria-label="Document navigation"><a href="/trust"><ArrowLeft size={16}/>Trust center</a><button type="button" onClick={onCopy}>{copied ? <Check size={16}/> : <Copy size={16}/>} {copied ? 'Copied' : 'Copy link'}</button></nav>
    <StudioHeader kicker="The fine print, made clear" title={title} description={description}/>
    <div className="pt-document-meta"><span>Last updated {updated}</span><a href={historyHref} target="_blank" rel="noreferrer"><History size={15}/>Version history<ArrowUpRight size={14}/></a></div>
    <div className="pt-document-layout">
      <aside className="pt-document-contents"><div className="pt-document-contents-label"><BookOpen size={17}/><span>In this document</span><small>{Math.round(progress)}%</small></div><div className="pt-document-progress"><div role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100} aria-label="Document reading progress" style={{width:`${progress}%`}}/></div><nav aria-label="Table of contents">{sections.map(section=><button type="button" key={section.id} onClick={()=>onSection(section.id)} aria-current={activeId === section.id ? 'location' : undefined}>{section.title}</button>)}</nav><a className="pt-document-question" href="/support">Something unclear?<span>We're here to help <ArrowUpRight size={14}/></span></a></aside>
      <article ref={articleRef} className="pt-document-paper"><div className="pt-document-body">{children}</div><nav className="pt-document-related" aria-label="Related documents">{[['Privacy policy','/privacy'],['Terms of service','/terms'],['Security','/security']].filter(([label])=>label.toLowerCase()!==title.toLowerCase()).map(([label,href])=><a key={href} href={href}>{label}<ArrowUpRight size={18}/></a>)}</nav></article>
    </div>
    <button type="button" className="pt-document-top" data-visible={showTop} onClick={onTop} aria-label="Back to top"><ArrowUp size={18}/></button>
  </StudioPage>;
}
