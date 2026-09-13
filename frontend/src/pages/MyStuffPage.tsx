/** A personal inventory of the passwords, reusable assets and preferences kept on this device. */
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ArrowRight, Download, Eye, EyeOff, FolderHeart, HardDrive, Image, KeyRound, Settings2, ShieldCheck, Trash2 } from "lucide-react";
import * as vault from "@/lib/localStore/vault";
import * as counters from "@/lib/localStore/counters";
import * as assets from "@/lib/localStore/assets";
import * as toolDefaults from "@/lib/localStore/defaults";
import { eraseEverything, exportSetup, inventory, type Inventory } from "@/lib/localStore/inventory";
import { downloadBlob } from "@/lib/api";
import { tools } from "@/data/tools";
import "@/skins/experience/workflows.css";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
function plural(count: number, noun: string): string { return `${count} ${noun}${count === 1 ? "" : "s"}`; }

export default function MyStuffPage() {
  const [inv, setInv] = useState<Inventory | null>(null);
  const [entries, setEntries] = useState<vault.VaultEntryMeta[]>([]);
  const [assetList, setAssetList] = useState<assets.AssetMeta[]>([]);
  const [counterList, setCounterList] = useState<counters.BatesCounter[]>([]);
  const [revealed, setRevealed] = useState<Record<string, string>>({});
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [shelf, setShelf] = useState<"all" | "passwords" | "assets" | "preferences">("all");

  const refresh = useCallback(async () => {
    const [next, passwords, savedAssets, savedCounters] = await Promise.all([inventory(), vault.listEntries(), assets.listAssets(), counters.listCounters()]);
    setInv(next); setEntries(passwords); setAssetList(savedAssets); setCounterList(savedCounters);
  }, []);
  useEffect(() => { void refresh().catch(() => setError("We couldn’t read this browser’s saved items. Please try reloading.")); }, [refresh]);

  const reveal = async (id: string) => {
    if (revealed[id]) { setRevealed(current => { const next = { ...current }; delete next[id]; return next; }); return; }
    try { const password = await vault.revealPassword(id); setRevealed(current => ({ ...current, [id]: password })); }
    catch { setError("This password can’t be read. Its encryption key may have been cleared from this browser."); }
  };
  const changeStoredItems = async (action: () => Promise<void>) => {
    setBusy(true); setError("");
    try { await action(); await refresh(); } catch { setError("That change could not be saved on this device. Please try again."); }
    finally { setBusy(false); }
  };
  const doExport = async () => {
    try { downloadBlob(await exportSetup(), "privatools-setup.json"); }
    catch { setError("Your setup could not be exported. Please try again."); }
  };
  const doErase = async () => { await changeStoredItems(async () => { await eraseEverything(); setRevealed({}); setConfirming(false); }); };
  const total = inv ? inv.vault.count + inv.assets.count + inv.counters.count + inv.defaults.count : 0;

  return <section className="pt-studio-page pt-library-page" aria-label="My Stuff">
    <header className="pt-studio-header pt-workflow-header">
      <div className="pt-workflow-heading"><p className="pt-studio-kicker">MY STUFF / A LITTLE SPACE OF YOUR OWN</p><h1><span className="wf-air-copy">Keep the useful things.</span><span className="wf-play-copy">Your little collection.</span></h1><p>Passwords, signatures, and the settings that make your next task feel familiar.</p></div>
      <div className="wf-library-seal"><HardDrive size={26} /><span>Stored on this device only<small>{inv ? `${total} saved ${total === 1 ? "item" : "items"}` : "Reading your local library…"}</small></span></div>
    </header>

    {(error || (inv && !inv.available.indexedDb) || (inv && !inv.available.webCrypto)) && <div className="wf-notice wf-notice-error" role="alert"><AlertTriangle size={18} /><p>{error || (!inv?.available.indexedDb ? "This browser is blocking local storage, so these items cannot be remembered between visits." : "WebCrypto is unavailable in this browser. Your password vault cannot be used here.")}</p></div>}
    {inv && inv.vault.unreadable > 0 && <div className="wf-notice wf-notice-error"><AlertTriangle size={18} /><div><p>{plural(inv.vault.unreadable, "saved password")} can&apos;t be read any more because the encryption key is missing.</p><button className="wf-text-button" disabled={busy} onClick={() => changeStoredItems(async () => { await vault.clearVault(); setRevealed({}); })}>Remove them</button></div></div>}

    {inv?.isEmpty && <section className="wf-library-welcome"><div className="wf-library-illustration" aria-hidden="true"><span><KeyRound size={30} /></span><span><Image size={32} /></span><span><Settings2 size={27} /></span></div><div><p className="wf-section-label">A FRESH START</p><h2>A home for your handy things.</h2><p>Nothing stored on this device yet. Save a password or a reusable asset in a tool, and find it here next time.</p><Link className="wf-button wf-button-primary" to="/my-stuff/vault">Save your first password <ArrowRight size={16} /></Link></div></section>}

    <div className="wf-library-toolbar"><div><FolderHeart size={20} /><h2>Your shelves</h2></div><div className="wf-library-tabs" role="group" aria-label="Filter your library">{([['all', 'Everything'], ['passwords', 'Passwords'], ['assets', 'Assets'], ['preferences', 'Preferences']] as const).map(([value, label]) => <button key={value} aria-pressed={shelf === value} onClick={() => setShelf(value)}>{label}</button>)}</div></div>
    <div className="wf-library-grid">
      {(shelf === "all" || shelf === "passwords") && <section className="wf-library-shelf wf-password-shelf"><header><span className="wf-library-icon"><KeyRound size={23} /></span><div><h3>Password vault</h3><p>{plural(inv?.vault.count ?? 0, "password")} · encrypted on this device</p></div><Link to="/my-stuff/vault" className="wf-text-button">Open <ArrowRight size={15} /></Link></header>
        {entries.length ? <div className="wf-library-items">{entries.map(entry => <article className="wf-library-item" key={entry.id}><div><strong>{entry.label}</strong><code>{revealed[entry.id] || "••••••••••"}</code></div><div className="wf-item-actions"><button disabled={busy} onClick={() => reveal(entry.id)} aria-label={`${revealed[entry.id] ? "Hide" : "Show"} ${entry.label}`}>{revealed[entry.id] ? <EyeOff size={17} /> : <Eye size={17} />}</button><button disabled={busy} aria-label={`Delete ${entry.label}`} onClick={() => changeStoredItems(() => vault.deleteEntry(entry.id))}><Trash2 size={16} /></button></div></article>)}</div> : <p className="wf-shelf-empty">Keep passwords for the PDFs you protect and unlock. You choose what to remember.</p>}
        {entries.length > 0 && <button className="wf-text-button wf-shelf-clear" disabled={busy} onClick={() => changeStoredItems(async () => { await vault.clearVault(); setRevealed({}); })}>Clear saved passwords</button>}
      </section>}
      {(shelf === "all" || shelf === "assets") && <section className="wf-library-shelf wf-assets-shelf"><header><span className="wf-library-icon"><Image size={24} /></span><div><h3>Reusable assets</h3><p>{plural(inv?.assets.count ?? 0, "file")} · {formatBytes(inv?.assets.bytes ?? 0)}</p></div></header>
        {assetList.length ? <div className="wf-library-items">{assetList.map(asset => <article className="wf-library-item" key={asset.id}><div><strong>{asset.name}</strong><span>{asset.kind} · {formatBytes(asset.bytes)}</span></div><div className="wf-item-actions"><button aria-label={`Download ${asset.name}`} onClick={async () => { try { const blob = await assets.getAssetBlob(asset.id); if (blob) downloadBlob(blob, asset.name); } catch { setError("This asset could not be downloaded. Please try again."); } }}><Download size={17} /></button><button aria-label={`Delete ${asset.name}`} disabled={busy} onClick={() => changeStoredItems(() => assets.deleteAsset(asset.id))}><Trash2 size={16} /></button></div></article>)}</div> : <p className="wf-shelf-empty">Your saved signature, logo, watermark, or letterhead can live here, ready for another document.</p>}
        {assetList.length > 0 && <button className="wf-text-button wf-shelf-clear" disabled={busy} onClick={() => changeStoredItems(assets.clearAssets)}>Clear assets</button>}
      </section>}
      {(shelf === "all" || shelf === "preferences") && <section className="wf-library-shelf wf-preferences-shelf"><header><span className="wf-library-icon"><Settings2 size={24} /></span><div><h3>Your tool preferences</h3><p>{plural(inv?.defaults.count ?? 0, "tool")} customized</p></div></header>{inv?.defaults.count ? <><div className="wf-default-chips">{inv.defaults.slugs.map(slug => <Link to={`${tools.some(tool => tool.slug === slug) ? "/tool/" : "/tools/"}${slug}`} key={slug}>{slug.replace(/-/g, " ")}<ArrowRight size={13} /></Link>)}</div><button className="wf-text-button wf-shelf-clear" disabled={busy} onClick={() => changeStoredItems(toolDefaults.clearAll)}>Reset tool preferences</button></> : <p className="wf-shelf-empty">When a tool remembers your choices, those settings appear here. Make your usual tasks a little quicker.</p>}</section>}
      {(shelf === "all" || shelf === "preferences") && <section className="wf-library-shelf wf-numbering-shelf"><header><span className="wf-library-icon"><FolderHeart size={24} /></span><div><h3>Document numbering</h3><p>{plural(inv?.counters.count ?? 0, "matter")} saved</p></div><Link to="/tool/bates-numbering" className="wf-text-button">Open <ArrowRight size={15} /></Link></header>{counterList.length ? <div className="wf-library-items">{counterList.map(counter => <div className="wf-library-item" key={counter.id}><div><strong>{counter.name}</strong><span>Next number</span></div><code>{counters.formatNext(counter)}</code></div>)}</div> : <p className="wf-shelf-empty">Pick up a Bates numbering sequence where you left it. Your next document gets the right number.</p>}</section>}
    </div>

    <section className="wf-library-control"><div><p className="wf-section-label">YOURS TO MANAGE</p><h2>Take your setup. Leave a clean slate.</h2><p>The export excludes your password vault. It includes tool settings, numbering, and an inventory of saved assets.</p></div><div className="wf-library-control-actions"><button className="wf-button" onClick={doExport}><Download size={16} /> Export my setup</button>{confirming ? <div className="wf-erase-confirm" role="alert"><p>This removes saved items from this device. There is no undo.</p><button className="wf-button wf-button-danger" disabled={busy} onClick={doErase}><Trash2 size={16} /> Yes, erase it all</button><button className="wf-text-button" disabled={busy} onClick={() => setConfirming(false)}>Cancel</button></div> : <button className="wf-text-button wf-danger-text" onClick={() => setConfirming(true)}><Trash2 size={15} /> Erase everything</button>}</div></section>
    <footer className="wf-library-footnote"><ShieldCheck size={20} /><p>These items stay in this browser and disappear if its site data is cleared. Password encryption protects against casual access, but cannot protect against malicious code running on this page. Read about our <Link to="/security">security approach</Link>.</p></footer>
  </section>;
}
