import { describe, expect, it, vi, afterEach, beforeEach } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Blob as NodeBlob } from "node:buffer";
import { zipSync, strToU8 } from "fflate";
import { csvToJson, jsonToCsv, parseCsv, detectDelimiter } from "./csv-json";
import { TextDiffUI } from "./TextDiffUI";
import { computeDiff } from "./text-diff";
import { bumpSemver, formatSql, nextCronRuns } from "./dev-formatters";
import { parseYaml, writeYaml, parseTomlConfig, writeToml } from "./config-codecs";
import { convertSubtitles } from "./subtitle-conversion";
import { MarkdownHtmlUI } from "./MarkdownHtmlUI";
import { simpleMarkdownToHtml } from "./markdown-render";
import { readZipDirectory } from "./zip-directory";
import { normalizeWebpageUrl } from "./webpage-url";
import { ToolCopyButton } from "./SpecialistTools";
import { Base64UI } from "./Base64UI";
import { JwtDecoderUI, TimestampConverterUI } from "./UtilityTools";
import { downloadBlob } from "@/lib/api";
import { consumeFileHandoffs, consumeFileHandoff } from "@/lib/file-handoff";
vi.mock("@/lib/file-handoff", () => ({consumeFileHandoffs:vi.fn().mockResolvedValue([]),consumeFileHandoff:vi.fn().mockResolvedValue(null)}));
vi.mock("@/lib/api", async original => ({...await original<typeof import("@/lib/api")>(),downloadBlob:vi.fn()}));
beforeEach(() => { vi.mocked(consumeFileHandoffs).mockResolvedValue([]); vi.mocked(consumeFileHandoff).mockResolvedValue(null); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });
describe("CSV data preservation", () => {
 it("round trips commas, quotes, newlines and later columns", () => { const input=[{name:'Alex, S.',note:'A "quote"\nnext line'},{name:"Sam",extra:"kept"}]; const csv=jsonToCsv(JSON.stringify(input),","); expect(JSON.parse(csvToJson(csv,","))).toEqual([{name:'Alex, S.',note:'A "quote"\nnext line',extra:""},{name:"Sam",note:"",extra:"kept"}]); });
 it("ignores quoted separators when detecting columns", () => expect(detectDelimiter('"a,b,c";d\n"one";two')).toBe(";"));
 it("retains whitespace", () => expect(parseCsv('a,b\n x , y ',",")[1]).toEqual([" x "," y "]));
 it.each(['a,a\n1,2','a,b\n1,2,3','a,b\n"unclosed,2'])('rejects malformed CSV %s', value => expect(() => csvToJson(value,",")).toThrow());
 it("rejects primitive rows", () => expect(() => jsonToCsv('[1,2]',",")).toThrow(/array of objects/));
});
describe("developer helpers", () => {
 it("preserves unchanged lines around insertions", () => expect(computeDiff("one\ntwo\nthree","one\nnew\ntwo\nthree").map(row=>row.type)).toEqual(["same","added","same","same"]));
 it("clears stale comparisons", () => { render(<TextDiffUI/>); fireEvent.change(screen.getByRole("textbox",{name:"A · Original"}),{target:{value:"a"}}); fireEvent.change(screen.getByRole("textbox",{name:"B · Modified"}),{target:{value:"b"}}); fireEvent.click(screen.getByRole("button",{name:"Compare"})); fireEvent.change(screen.getByRole("textbox",{name:"A · Original"}),{target:{value:"updated"}}); expect(screen.queryByRole("group",{name:"Diff view"})).not.toBeInTheDocument(); });
 it("protects SQL strings and comments", () => { const output=formatSql(`select 'a,  b AND c' as "order by", x from items -- keep  this, SELECT\nwhere x=1`); expect(output).toContain("'a,  b AND c'"); expect(output).toContain('"order by"'); expect(output).toContain('-- keep  this, SELECT\n'); });
 it("advances prereleases and promotes releases", () => { expect(bumpSemver("1.2.3-beta.4+build.9","prerelease")).toBe("1.2.3-beta.5"); expect(bumpSemver("1.2.3-beta.4","patch")).toBe("1.2.3"); expect(() => bumpSemver("01.2.3","major")).toThrow(); });
 it("ORs restricted day-of-month and weekday", () => { const runs=nextCronRuns("0 9 13 * 1",new Date(2024,4,10,12)); expect(runs[0].getDate()).toBe(13); expect(runs[1].getDate()).toBe(20); });
 it("rejects malformed cron steps", () => expect(()=>nextCronRuns("*/2/3 * * * *")).toThrow());
});
describe("config conversions", () => {
 it("preserves comments inside strings, lists and scalar types", () => { const data={name:"true",note:"tea # break",nested:{count:12,enabled:false},items:["a,b","12",null]}; expect(parseYaml(writeYaml(data))).toEqual(data); });
 it("reads list maps", () => expect(parseYaml("items:\n  - name: Alex\n    city: Chennai\n  - name: Sam\n    city: Berlin")).toEqual({items:[{name:"Alex",city:"Chennai"},{name:"Sam",city:"Berlin"}]}));
 it("does not mutate prototypes", () => { const parsed=parseYaml("__proto__:\n  safe: true"); expect(Object.prototype.hasOwnProperty.call(parsed,"__proto__")).toBe(true); expect(({} as {safe?:boolean}).safe).toBeUndefined(); });
 it.each(['a: 1\na: 2','text: |\n  multiline','a: &anchor text','a: 1\n---\nb: 2'])('rejects lossy YAML %s', value => expect(()=>parseYaml(value)).toThrow());
 it("round trips TOML arrays with comma-containing strings", () => { const parsed=parseTomlConfig('[app]\nname = "a # b"\nports = [80, 443]\nlabels = ["x,y", "true"]'); expect(parsed).toEqual({app:{name:"a # b",ports:[80,443],labels:["x,y","true"]}}); expect(parseTomlConfig(writeToml(parsed))).toEqual(parsed); });
 it("rejects TOML null", () => expect(()=>writeToml({value:null})).toThrow(/no null/));
});
describe("subtitles and files", () => {
 it("reads VTT cue identifiers and short timestamps", () => expect(convertSubtitles("WEBVTT\n\nintro\n00:01.500 --> 00:03.200\nHello", "srt").output).toContain("00:00:01,500 --> 00:00:03,200"));
 it("retains ASS centiseconds", () => expect(convertSubtitles("Dialogue: 0,0:00:01.50,0:00:03.25,Default,,0,0,0,,Hello","vtt").output).toContain("00:00:01.500 --> 00:00:03.250"));
 it("rejects reversed cue timing", () => expect(convertSubtitles("1\n00:00:04,000 --> 00:00:01,000\nHello","vtt").ok).toBe(false));
 it("normalizes HTTP only", () => { expect(normalizeWebpageUrl(" example.com ")).toBe("https://example.com/"); expect(normalizeWebpageUrl("HTTP://example.com")).toBe("http://example.com/"); expect(normalizeWebpageUrl("javascript:alert(1)")).toBeNull(); });
 it("lists ZIP metadata without inflating payloads", async () => { const bytes=zipSync({"one.txt":strToU8("one"),"folder/two.txt":strToU8("two")}); const directory=await readZipDirectory(new NodeBlob([bytes]) as unknown as Blob); expect(directory.entries.map(entry=>[entry.name,entry.bytes])).toEqual([["one.txt",3],["folder/two.txt",3]]); });
});
describe("Markdown editing", () => {
 it("renders lists/code and refuses executable links", () => { const html=simpleMarkdownToHtml('# Hello\n\n- One\n- Two\n\n```\n<script>alert(1)</script>\n```\n\n[run](javascript:alert)'); expect(html).toContain('<ul>'); expect(html).toContain('&lt;script&gt;'); expect(html).not.toContain('href="javascript:'); });
 it("opens MD, preserves editor across views and saves source", async () => { render(<MarkdownHtmlUI/>); const file=new File([],"notes.md",{type:"text/markdown"}); Object.defineProperty(file,"text",{value:()=>Promise.resolve("# Loaded\n\nA real draft.")}); fireEvent.change(screen.getByLabelText("Open Markdown file"),{target:{files:[file]}}); await waitFor(()=>expect(screen.getByRole("textbox",{name:"Markdown source"})).toHaveValue("# Loaded\n\nA real draft.")); const node=screen.getByRole("textbox",{name:"Markdown source"}); fireEvent.click(screen.getByRole("button",{name:"HTML output"})); expect(screen.getByRole("textbox",{name:"Markdown source"})).toBe(node); expect(screen.getByTitle("Markdown preview")).toHaveAttribute("sandbox",""); fireEvent.click(screen.getByRole("button",{name:"Save Markdown"})); expect(downloadBlob).toHaveBeenCalledWith(expect.any(Blob),"notes.md"); });
 it("preserves draft on a read failure", async () => { render(<MarkdownHtmlUI/>); const node=screen.getByRole("textbox",{name:"Markdown source"}); const before=(node as HTMLTextAreaElement).value; const file=new File([],"broken.md"); Object.defineProperty(file,"text",{value:()=>Promise.reject(new Error("Read failed"))}); fireEvent.change(screen.getByLabelText("Open Markdown file"),{target:{files:[file]}}); await screen.findByRole("alert"); expect(node).toHaveValue(before); });
});
describe("truthful feedback", () => {
 it("reports clipboard rejection without claiming success", async () => { Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:vi.fn().mockRejectedValue(new Error("blocked"))}}); render(<ToolCopyButton value="example"/>); fireEvent.click(screen.getByRole("button",{name:"Copy"})); expect(await screen.findByRole("status")).toHaveTextContent("Copy unavailable"); expect(screen.queryByRole("button",{name:"Copied"})).not.toBeInTheDocument(); });
 it("encodes whitespace", async () => { render(<Base64UI/>); fireEvent.change(screen.getByRole("textbox",{name:"Base64 source"}),{target:{value:"  "}}); await waitFor(()=>expect(screen.getByLabelText("Base64 result")).toHaveTextContent("ICA=")); });
 it("handles extreme JWT dates without verifying a signature", () => { render(<JwtDecoderUI/>); fireEvent.change(screen.getByRole("textbox",{name:"JWT token"}),{target:{value:[btoa('{"alg":"none"}'),btoa('{"exp":1e100}'),"signature"].join(".")}}); expect(screen.getByText("Date outside supported range")).toBeInTheDocument(); expect(screen.getByText("Signature · not verified")).toBeInTheDocument(); });
 it("supports milliseconds near the epoch", () => { render(<TimestampConverterUI/>); fireEvent.change(screen.getByRole("textbox",{name:"Timestamp or date"}),{target:{value:"1000"}}); fireEvent.change(screen.getByRole("combobox",{name:"Timestamp unit"}),{target:{value:"ms"}}); expect(screen.getByText("1970-01-01T00:00:01.000Z")).toBeInTheDocument(); });
});
