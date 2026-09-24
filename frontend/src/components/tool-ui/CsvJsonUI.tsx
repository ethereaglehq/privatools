import { type Delimiter, parseCsv, detectDelimiter, csvToJson, jsonToCsv } from "./csv-json";
import { useMemo, useState } from "react";
import { ArrowLeftRight, Download, Sparkles } from "lucide-react";
import { downloadBlob } from "@/lib/api";
import { emitToolRun } from "@/lib/toolRun";
import { useToolDefaults } from "@/hooks/useToolDefaults";
import { LabPair, LabOutput, LabWorkspace, ToolCopyButton } from "./SpecialistTools";
type Mode = "csv-to-json" | "json-to-csv";
const LABELS: Record<Delimiter, string> = { ",": "Comma", ";": "Semicolon", "\t": "Tab", "|": "Pipe" };
const DEFAULTS: { mode: Mode } = { mode: "csv-to-json" };
export function CsvJsonUI() {
    const [config, , { setField }] = useToolDefaults("csv-json", DEFAULTS);
    const { mode } = config;
    const [input, setInput] = useState("");
    const [output, setOutput] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [override, setOverride] = useState<Delimiter | null>(null);
    const detected = useMemo(() => detectDelimiter(input), [input]);
    const delimiter = override ?? (mode === "csv-to-json" ? detected : ",");
    const resetResult = () => { setOutput(null); setError(null); };
    const run = () => { resetResult(); try { setOutput(mode === "csv-to-json" ? csvToJson(input, delimiter) : jsonToCsv(input, delimiter)); emitToolRun({ outcome: "success" }); } catch (e) { setError(e instanceof Error ? e.message : "Couldn't convert this input."); emitToolRun({ outcome: "error", errorKind: "bad_input" }, e); } };
    return <LabWorkspace kind="csv" note="Your table is converted on this device. Quoted fields and line breaks are preserved; CSV values stay as strings.">
        <div className="pt-lab-toolbar"><div role="group" className="pt-lab-tabs" aria-label="Table conversion direction">{(["csv-to-json", "json-to-csv"] as const).map(value => <button key={value} aria-pressed={mode === value} onClick={() => { setField("mode", value); resetResult(); }}>{value === "csv-to-json" ? "CSV to JSON" : "JSON to CSV"}</button>)}</div><button className="pt-lab-button" onClick={() => { setInput(mode === "csv-to-json" ? 'name,city,note\nAlex,Chennai,"Tea, then work"\nSam,Berlin,"A fresh start"' : '[\n  {"name":"Alex","city":"Chennai"},\n  {"name":"Sam","city":"Berlin","note":"A fresh start"}\n]'); setOverride(null); resetResult(); }}><Sparkles size={15}/>Try sample</button></div>
        <LabPair input={<><label className="pt-lab-field"><span>{mode === "csv-to-json" ? "Your table" : "Your JSON records"}</span><textarea className="pt-lab-textarea" aria-label="Table source" value={input} onChange={e => { setInput(e.target.value); resetResult(); }} onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); run(); } }} spellCheck={false} placeholder={mode === "csv-to-json" ? "name,city\nAlex,Chennai" : '[{"name":"Alex","city":"Chennai"}]'}/></label><label className="pt-lab-select-label">{mode === "csv-to-json" ? "Read columns separated by" : "Separate columns with"}<select aria-label="CSV delimiter" value={override ?? "auto"} onChange={e => { setOverride(e.target.value === "auto" ? null : e.target.value as Delimiter); resetResult(); }}><option value="auto">{mode === "csv-to-json" ? `Auto · ${LABELS[detected]}` : "Default · Comma"}</option>{Object.entries(LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><button className="pt-lab-button is-primary" onClick={run} disabled={!input.trim()}><ArrowLeftRight size={16}/>Convert {mode === "csv-to-json" ? "to JSON" : "to CSV"}</button></>} output={<><div className="pt-lab-toolbar"><h2>{mode === "csv-to-json" ? "Structured and ready" : "Your portable table"}</h2><ToolCopyButton value={output ?? ""}/></div>{error ? <p role="alert" className="pt-lab-issue is-error">{error}</p> : <LabOutput label="Converted table" value={output ?? ""}/>} {output !== null && <div className="pt-lab-controls pt-lab-spaced"><button className="pt-lab-button" onClick={() => downloadBlob(new Blob([output], {type: mode === "csv-to-json" ? "application/json" : "text/csv"}), `converted.${mode === "csv-to-json" ? "json" : "csv"}`)}><Download size={15}/>Download {mode === "csv-to-json" ? ".json" : ".csv"}</button>{output === "" && <span className="pt-lab-caption">The input contains no records.</span>}</div>}</>}/>
    </LabWorkspace>;
}
