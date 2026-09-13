import { type Rect, positionTourCard } from "./tour-position";
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useLocation } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, X } from "lucide-react";
import { TOTAL_TOOL_COUNT } from "@/data/site-stats";
import { START_TOUR_EVENT } from "@/lib/events";
import "./onboarding-tour.css";

const STORAGE_KEY = "privatools_onboarding_done";
interface TourStep { id: string; selectors: string[]; label: string; title: string; description: string }
const tourSteps: TourStep[] = [
  { id: "tools", selectors: ['.pt-top-links [data-destination="tools"]'], label: "All tools", title: "Find your next little helper.", description: `Start here for all ${TOTAL_TOOL_COUNT} tools. Browse PDFs, images, video, text and more. File tools are free to use without signing in; each workspace tells you where processing happens.` },
  { id: "search", selectors: [".pt-search-trigger", ".pt-home-search"], label: "Search", title: "A task in mind? Just search.", description: "Try a task like “compress a PDF” or “resize an image”. On a keyboard, ⌘K or Ctrl+K opens tool search from anywhere." },
  { id: "pipeline", selectors: ['.pt-top-links [data-destination="pipeline"]'], label: "Pipeline", title: "Put the steps in order.", description: "Build a sequence of compatible tools, adjust each step, then run it. Save a recipe when you find a routine you want to use again." },
  { id: "batch", selectors: ['.pt-top-links [data-destination="batch"]'], label: "Batch", title: "One task. A few more files.", description: "Choose a supported tool and apply its settings to a collection of files. Follow each result in the queue, retry a failed item, or cancel a run." },
  { id: "ai", selectors: ['.pt-top-links [data-destination="ai"]'], label: "AI Studio", title: "A little help with the reading.", description: "Explore document chat, summaries and other AI tasks. Check the chosen model or provider before sharing a file; availability and processing location depend on that choice." },
  { id: "vault", selectors: ['.pt-top-links [data-destination="vault"]'], label: "Vault", title: "Keep useful details nearby.", description: "Save reusable PDF passwords and assets on this device. Your Vault works as a guest and stays in this browser; it isn’t a cloud backup or an account sync." },
  { id: "mystuff", selectors: ['.pt-top-links [data-destination="mystuff"]'], label: "My Stuff", title: "Your own small collection.", description: "Find the recipes, assets and settings you’ve saved locally. My Stuff works without an account. You can export or remove saved items, and clearing browser storage can remove them." },
  { id: "api", selectors: ['.pt-top-links [data-destination="api"]'], label: "Dev API", title: "For the things you automate.", description: "Read the API guide and request examples here. Creating and managing API keys needs an account; ordinary file tools remain open to guests." },
  { id: "style", selectors: [".pt-header .pt-style-switch"], label: "Air / Play", title: "Make the place feel like you.", description: "Air keeps things calm and spacious. Play adds warmer shapes and a little bounce. Switch between them here; your current files and task stay with you." },
  { id: "theme", selectors: [".pt-header .pt-theme-toggle"], label: "Light / dark", title: "Settle into your shade.", description: "This sun or moon button switches light and dark in one click. Air has Morning Mist and Graphite; Play has Blush and Charcoal. You can replay this tour from the footer whenever you like." },
];

function findTarget(step: TourStep) {
  for (const selector of step.selectors) {
    for (const candidate of document.querySelectorAll<HTMLElement>(selector)) {
      const bounds = candidate.getBoundingClientRect();
      if (bounds.width > 0 && bounds.height > 0 && getComputedStyle(candidate).visibility !== "hidden") return candidate;
    }
  }
  return null;
}

function revealTarget(anchor: HTMLElement | null) {
  anchor?.scrollIntoView({ block: "nearest", inline: "center", behavior: "instant" });
  // Body controls must clear the sticky header after native scrolling.
  const header = document.querySelector(".pt-header");
  if (anchor && !header?.contains(anchor)) {
    const desiredTop = (header?.getBoundingClientRect().bottom ?? 0) + 24;
    window.scrollBy({ top: anchor.getBoundingClientRect().top - desiredTop, behavior: "instant" });
  }
}

export function OnboardingTour() {
  const location = useLocation();
  const [activeSteps, setActiveSteps] = useState<TourStep[]>([]);
  const [index, setIndex] = useState(0);
  const [targetRect, setTargetRect] = useState<Rect | null>(null);
  const [viewport, setViewport] = useState({ width: window.innerWidth, height: window.innerHeight });
  const [cardSize, setCardSize] = useState({ width: 360, height: 310 });
  const dialog = useRef<HTMLDivElement>(null);
  const nextButton = useRef<HTMLButtonElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);
  const target = useRef<HTMLElement | null>(null);
  const show = activeSteps.length > 0;
  const current = activeSteps[index];
  const maskId = `tour-mask-${useId().replace(/:/g, "")}`;
  const dismiss = useCallback(() => {
    setActiveSteps([]);
    try { localStorage.setItem(STORAGE_KEY, "1"); } catch { /* Dismissal still works when storage is unavailable. */ }
  }, []);
  const start = useCallback(() => {
    const available = tourSteps.filter(step => findTarget(step));
    if (!available.length) return;
    previouslyFocused.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setIndex(0);
    setTargetRect(null);
    setActiveSteps(available);
  }, []);

  useEffect(() => {
    window.addEventListener(START_TOUR_EVENT, start);
    return () => window.removeEventListener(START_TOUR_EVENT, start);
  }, [start]);

  useEffect(() => {
    // No automatic first-visit popup. Existing dismissal preferences persist;
    // an explicit replay event or tour URL is the visitor asking to open it.
    if (location.pathname !== "/") return;
    const url = new URL(window.location.href);
    if (url.searchParams.get("tour") !== "1" && url.hash !== "#tour") return;
    const timer = window.setTimeout(start, 250);
    return () => window.clearTimeout(timer);
  }, [location.pathname, start]);

  useEffect(() => { setActiveSteps([]); }, [location.pathname]);

  useEffect(() => {
    if (!show) {
      if (previouslyFocused.current?.isConnected) previouslyFocused.current.focus();
      previouslyFocused.current = null;
      return;
    }
    const frame = requestAnimationFrame(() => nextButton.current?.focus({ preventScroll: true }));
    const keyDown = (event: KeyboardEvent) => {
      // Keep site-wide shortcuts from opening another overlay underneath.
      event.stopPropagation();
      if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); dismiss(); }
      if (event.key !== "Tab" || !dialog.current) return;
      const buttons = [...dialog.current.querySelectorAll<HTMLElement>('button:not([disabled]), [href], [tabindex="0"]')];
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (!dialog.current.contains(document.activeElement) || event.shiftKey && document.activeElement === first || !event.shiftKey && document.activeElement === last) {
        event.preventDefault(); (event.shiftKey ? last : first)?.focus();
      }
    };
    document.addEventListener("keydown", keyDown, true);
    return () => { cancelAnimationFrame(frame); document.removeEventListener("keydown", keyDown, true); };
  }, [show, dismiss]);

  useLayoutEffect(() => {
    if (!show || !current) return;
    let frame = 0;
    const anchor = findTarget(current);
    target.current = anchor;
    anchor?.setAttribute("data-tour-target", current.id);
    // Native scrolling also reveals items in the mobile horizontal navigation.
    revealTarget(anchor);
    const measure = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const width = window.visualViewport?.width ?? window.innerWidth;
        const height = window.visualViewport?.height ?? window.innerHeight;
        setViewport({ width, height });
        const active = findTarget(current);
        if (active !== target.current) {
          target.current?.removeAttribute("data-tour-target");
          target.current = active;
          active?.setAttribute("data-tour-target", current.id);
          revealTarget(active);
        }
        const bounds = active?.getBoundingClientRect();
        if (bounds && bounds.bottom > 0 && bounds.top < height && bounds.right > 0 && bounds.left < width) {
          setTargetRect({ left: Math.max(4, bounds.left - 5), top: Math.max(4, bounds.top - 5), width: Math.min(width - 4, bounds.right + 5) - Math.max(4, bounds.left - 5), height: Math.min(height - 4, bounds.bottom + 5) - Math.max(4, bounds.top - 5) });
        } else setTargetRect(null);
        if (dialog.current) {
          const rect = dialog.current.getBoundingClientRect();
          setCardSize(previous => Math.abs(previous.height - rect.height) > 1 || Math.abs(previous.width - rect.width) > 1 ? { width: rect.width, height: rect.height } : previous);
        }
      });
    };
    measure();
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(measure) : null;
    if (anchor) observer?.observe(anchor);
    if (dialog.current) observer?.observe(dialog.current);
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    window.visualViewport?.addEventListener("resize", measure);
    const focusFrame = requestAnimationFrame(() => nextButton.current?.focus({ preventScroll: true }));
    return () => {
      cancelAnimationFrame(frame); cancelAnimationFrame(focusFrame);
      observer?.disconnect();
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
      window.visualViewport?.removeEventListener("resize", measure);
      target.current?.removeAttribute("data-tour-target"); target.current = null;
    };
  }, [show, current]);

  if (!show || !current) return null;
  const position = positionTourCard(targetRect, viewport, { width: Math.min(viewport.height < 500 ? 280 : 360, viewport.width - 24), height: cardSize.height });
  const last = index === activeSteps.length - 1;
  return createPortal(<div className="pt-tour" data-step={current.id}>
    <div className="pt-tour-shield" aria-hidden="true"/>
    <svg className="pt-tour-dimmer" width="100%" height="100%" aria-hidden="true"><defs><mask id={maskId}><rect width="100%" height="100%" fill="white"/>{targetRect && <rect width={targetRect.width} height={targetRect.height} x={targetRect.left} y={targetRect.top} rx="10" fill="black"/>}</mask></defs><rect width="100%" height="100%" mask={`url(#${maskId})`}/></svg>
    {targetRect && <div className="pt-tour-spotlight" style={{ left: targetRect.left, top: targetRect.top, width: targetRect.width, height: targetRect.height }} aria-hidden="true"/>}
    <div ref={dialog} className="pt-tour-card" role="dialog" aria-modal="true" aria-labelledby="tour-title" aria-describedby="tour-description" style={{ left: position.left, top: position.top, width: position.width, maxHeight: viewport.height - 24 }} data-side={position.side}>
      {targetRect && position.side !== "floating" && <span className="pt-tour-pointer" style={position.side === "left" || position.side === "right" ? { top: position.arrowTop } : { left: position.arrowLeft }} aria-hidden="true"/>}
      <div className="pt-tour-card-inner"><header><span className="pt-tour-step-label">A little look around <span>{index + 1} / {activeSteps.length}</span></span><button type="button" className="pt-tour-close" aria-label="Close tour" onClick={dismiss}><X size={17}/></button></header>
        <div className="pt-tour-copy" key={current.id}><span className="pt-tour-control-label">{current.label}</span><h2 id="tour-title">{current.title}</h2><p id="tour-description">{current.description}</p>{!targetRect && <button type="button" className="pt-tour-reveal" onClick={() => revealTarget(findTarget(current))}>Bring this control into view</button>}</div>
        <div className="pt-tour-progress" role="progressbar" aria-label="Tour progress" aria-valuemin={1} aria-valuemax={activeSteps.length} aria-valuenow={index + 1}>{activeSteps.map((step, stepIndex) => <span key={step.id} data-complete={stepIndex <= index || undefined}/>)}</div>
        <footer><button type="button" className="pt-tour-skip" onClick={dismiss}>Skip tour</button><div><button type="button" className="pt-tour-back" disabled={index === 0} onClick={() => setIndex(value => value - 1)}><ArrowLeft size={15}/><span>Back</span></button><button ref={nextButton} type="button" className="pt-tour-next" onClick={() => last ? dismiss() : setIndex(value => value + 1)}>{last ? <>All set <Check size={16}/></> : <>Next <ArrowRight size={16}/></>}</button></div></footer>
      </div>
    </div>
  </div>, document.body);
}
