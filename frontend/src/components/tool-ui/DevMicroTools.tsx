import { formatSql, formatGraphql, describeCronField, nextCronRuns, bumpSemver } from "./dev-formatters";
import { parseYaml, writeYaml, parseTomlConfig, writeToml } from "./config-codecs";
import { useMemo, useState, type ReactNode } from "react";
import { Check, Copy, Download, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { LabWorkspace, LabNote, LabPair, LabOutput, ToolCopyButton } from "./SpecialistTools";

type IssueLevel = "ok" | "warn" | "error";

const CopyButton = ToolCopyButton;

function DownloadButton({ value, filename, label = "Download" }: { value: string; filename: string; label?: string }) {
  return (
    <button
      type="button"
      disabled={!value}
      onClick={() => {
        const blob = new Blob([value], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
      }}
      className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-card px-3 text-[13px] font-medium text-foreground transition-colors hover:bg-secondary/60 disabled:opacity-45"
    >
      <Download size={14} />
      {label}
    </button>
  );
}

function ClientOnlyNote({ children }: { children: string }) { return <LabNote>{children}</LabNote>; }

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="pt-lab-field">
      <span className="pt-lab-field-label">{label}</span>
      {children}
    </label>
  );
}

function TextArea({
  value,
  onChange,
  rows = 12,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <textarea
      value={value}
      onChange={e => onChange(e.target.value)}
      rows={rows}
      spellCheck={false}
      placeholder={placeholder}
      className="pt-lab-textarea"
    />
  );
}

function OutputBox({ value }: { value: string; minHeight?: string }) { return <LabOutput value={value} />; }

function SplitTool({
  note,
  left,
  right,
}: {
  note: string;
  left: React.ReactNode;
  right: React.ReactNode;
}) {
  return <LabWorkspace note={note} kind="code"><LabPair input={left} output={right} /></LabWorkspace>;
}

function statusClass(level: IssueLevel) { return `pt-lab-issue is-${level}`; }

function flattenObject(value: unknown, prefix = "", out: Record<string, unknown> = {}) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
      flattenObject(nested, prefix ? `${prefix}.${key}` : key, out);
    }
  } else {
    out[prefix] = value;
  }
  return out;
}

function csvEscape(value: unknown) {
  const text = value == null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function inferType(values: unknown[]) {
  const present = values.filter(v => v !== undefined && v !== null && v !== "");
  if (!present.length) return "empty";
  if (present.every(v => typeof v === "boolean" || /^(true|false)$/i.test(String(v)))) return "boolean";
  if (present.every(v => Number.isFinite(Number(v)))) return "number";
  if (present.every(v => !Number.isNaN(Date.parse(String(v))))) return "date";
  return "string";
}

export function CronParserUI() {
  const [expr, setExpr] = useState("*/15 9-17 * * 1-5");
  const result = useMemo(() => {
    try {
      const parts = expr.trim().split(/\s+/);
      const runs = nextCronRuns(expr);
      return {
        level: "ok" as IssueLevel,
        summary: [
          describeCronField(parts[0], "Minute", "minute"),
          describeCronField(parts[1], "Hour", "hour"),
          describeCronField(parts[2], "Day of month", "day"),
          describeCronField(parts[3], "Month", "month"),
          describeCronField(parts[4], "Weekday", "weekday"),
        ],
        output: runs.map(date => date.toLocaleString()).join("\n") || "No matching run found in the next year.",
      };
    } catch (error) {
      return { level: "error" as IssueLevel, summary: [(error as Error).message], output: "" };
    }
  }, [expr]);
  return <LabWorkspace kind="cron" note="Standard five-field cron, calculated locally in your browser’s time zone."><div className="pt-lab-schedule"><section><h2>When should it run?</h2><Field label="Cron expression"><input value={expr} onChange={e => setExpr(e.target.value)} aria-invalid={result.level === "error"} /></Field><p className="pt-lab-caption">Minute · hour · day · month · weekday</p><ul aria-label="Schedule meaning">{result.summary.map(item => <li key={item}>{item}</li>)}</ul>{result.level === "error" && <p role="alert" className="pt-lab-issue is-error">Check the expression above.</p>}</section><section><div className="pt-lab-toolbar"><div><h2>Your next five runs</h2><p>{Intl.DateTimeFormat().resolvedOptions().timeZone}</p></div><CopyButton value={result.level === "ok" ? result.output : ""} /></div><LabOutput value={result.output} label="Next scheduled runs"/><p className="pt-lab-caption">These are previews. PrivaTools does not schedule or run this job.</p></section></div></LabWorkspace>;
}

export function SqlFormatterUI() {
  const [input, setInput] = useState("select id, email, created_at from users where active = true and created_at > now() - interval '30 days' order by created_at desc limit 25;");
  const output = useMemo(() => formatSql(input), [input]);
  return (
    <SplitTool
      note="Formats SQL text in the browser with keyword line breaks and readable clause grouping."
      left={<Field label="SQL input"><TextArea value={input} onChange={setInput} /></Field>}
      right={<><div className="pt-lab-toolbar"><span className="pt-lab-result-label">Formatted SQL</span><CopyButton value={output} /></div><OutputBox value={output} /></>}
    />
  );
}

export function GraphqlFormatterUI() {
  const [input, setInput] = useState("query User($id: ID!){user(id:$id){id name posts(first:5){nodes{id title}}}}");
  const output = useMemo(() => formatGraphql(input), [input]);
  return (
    <SplitTool
      note="Pretty-prints GraphQL queries, mutations, fragments, and selection sets without sending them anywhere."
      left={<Field label="GraphQL input"><TextArea value={input} onChange={setInput} /></Field>}
      right={<><div className="pt-lab-toolbar"><span className="pt-lab-result-label">Formatted GraphQL</span><CopyButton value={output} /></div><OutputBox value={output} /></>}
    />
  );
}

export function YamlTomlConverterUI() {
  const [mode, setMode] = useState<"yaml-to-toml" | "toml-to-yaml">("yaml-to-toml");
  const [input, setInput] = useState("app:\n  name: privatools\n  port: 8000\nfeatures:\n  localOnly: true\n  retries: 3");
  const converted = useMemo(() => {
    try {
      return mode === "yaml-to-toml" ? writeToml(parseYaml(input)) : writeYaml(parseTomlConfig(input));
    } catch (error) {
      return `Error: ${(error as Error).message}`;
    }
  }, [input, mode]);
  return (
    <div className="pt-specialist pt-dev-specialist space-y-4">
      <ClientOnlyNote>Converts common flat and nested config shapes between YAML and TOML locally.</ClientOnlyNote>
      <div className="inline-flex rounded-lg border border-border bg-card p-1">
        {(["yaml-to-toml", "toml-to-yaml"] as const).map(option => (
          <button key={option} type="button" onClick={() => setMode(option)} className={cn("rounded-md px-3 py-1.5 text-[13px] font-medium", mode === option ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground")}>
            {option === "yaml-to-toml" ? "YAML to TOML" : "TOML to YAML"}
          </button>
        ))}
      </div>
      <SplitTool
        note="Supports nested mappings, scalar arrays and strings. Comments are omitted; unsupported anchors, multiline values and array tables produce an error."
        left={<Field label={mode === "yaml-to-toml" ? "YAML input" : "TOML input"}><TextArea value={input} onChange={setInput} /></Field>}
        right={<><div className="pt-lab-toolbar"><span className="pt-lab-result-label">Converted config</span><CopyButton value={converted.startsWith("Error:") ? "" : converted} /></div>{converted.startsWith("Error:") ? <p role="alert" className="pt-lab-issue is-error">{converted}</p> : <OutputBox value={converted} />}</>}
      />
    </div>
  );
}

const GITIGNORE_TEMPLATES: Record<string, string[]> = {
  Node: ["node_modules/", "dist/", "build/", ".env", ".env.*", "npm-debug.log*", "pnpm-debug.log*", "yarn-debug.log*"],
  Python: ["__pycache__/", "*.py[cod]", ".pytest_cache/", ".mypy_cache/", ".venv/", "venv/", "dist/", "*.egg-info/"],
  Vite: ["dist/", "dist-ssr/", "*.local"],
  Next: [".next/", "out/", "next-env.d.ts"],
  Docker: [".docker/", "docker-compose.override.yml", "*.pid"],
  macOS: [".DS_Store", ".AppleDouble", ".LSOverride"],
  Windows: ["Thumbs.db", "Desktop.ini", "$RECYCLE.BIN/"],
  Terraform: [".terraform/", "*.tfstate", "*.tfstate.*", ".terraform.lock.hcl"],
  Go: ["bin/", "*.test", "coverage.out"],
  Rust: ["target/", "Cargo.lock"],
};

export function GitignoreGeneratorUI() {
  const [selected, setSelected] = useState<string[]>(["Node", "Vite", "macOS"]);
  const output = useMemo(() => selected.map(name => `# ${name}\n${GITIGNORE_TEMPLATES[name].join("\n")}`).join("\n\n"), [selected]);
  return (
    <div className="pt-specialist pt-dev-specialist space-y-4">
      <ClientOnlyNote>Generates a ready-to-save .gitignore from bundled templates. No external template API is called.</ClientOnlyNote>
      <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-2xl border border-border bg-card/60 p-4">
          <p className="font-medium mb-3 text-[11.5px] text-muted-foreground">Templates</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.keys(GITIGNORE_TEMPLATES).map(name => (
              <label key={name} className={cn("flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-[13px]", selected.includes(name) ? "border-accent/50 bg-accent/[0.07]" : "border-border hover:bg-secondary/50")}>
                <input type="checkbox" className="accent-[hsl(var(--accent))]" checked={selected.includes(name)} onChange={e => setSelected(prev => e.target.checked ? [...prev, name] : prev.filter(item => item !== name))} />
                {name}
              </label>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card/60 p-4">
          <div className="pt-lab-toolbar">
            <span className="pt-lab-result-label">.gitignore</span>
            <div className="flex gap-2"><CopyButton value={output} /><DownloadButton value={output} filename=".gitignore" /></div>
          </div>
          <OutputBox value={output} />
        </div>
      </div>
    </div>
  );
}

export function SemverBumperUI() {
  const [version, setVersion] = useState("1.4.9");
  const result = useMemo(() => { try { return { rows: (["patch", "minor", "major", "prerelease"] as const).map(kind => ({ kind, value: bumpSemver(version, kind) })), error: "" }; } catch (e) { return { rows: [], error: (e as Error).message }; } }, [version]);
  return <LabWorkspace kind="versions" note="Choose the size of your next release. This changes the preview only."><div className="pt-lab-input-pane"><Field label="Current version"><input value={version} onChange={e => setVersion(e.target.value)} aria-invalid={!!result.error} className="pt-lab-version-input" /></Field>{result.error && <p role="alert" className="pt-lab-issue is-error">{result.error}</p>}</div><div className="pt-lab-release-grid">{result.rows.map(({kind,value}) => <section className="pt-lab-release" key={kind}><div><strong>{kind}</strong><CopyButton value={value}/></div><p>{value}</p></section>)}</div><p className="pt-lab-caption">Prerelease starts at beta.1 for the next patch. Build metadata is removed when a version changes.</p></LabWorkspace>;
}

function parseEnv(input: string) {
  const issues: Array<{ level: IssueLevel; text: string }> = [];
  const seen = new Map<string, number>();
  const validName = /^[A-Za-z_][A-Za-z0-9_]*$/;
  input.split(/\r?\n/).forEach((raw, index) => {
    const lineNo = index + 1;
    const line = raw.trim();
    if (!line || line.startsWith("#")) return;
    const eq = line.indexOf("=");
    if (eq < 0) {
      issues.push({ level: "error", text: `Line ${lineNo}: missing =` });
      return;
    }
    const key = line.slice(0, eq).trim();
    const value = line.slice(eq + 1);
    if (!validName.test(key)) issues.push({ level: "error", text: `Line ${lineNo}: invalid variable name ${key}` });
    if (seen.has(key)) issues.push({ level: "warn", text: `Line ${lineNo}: duplicate key ${key}, first seen on line ${seen.get(key)}` });
    seen.set(key, lineNo);
    if (value === "") issues.push({ level: "warn", text: `Line ${lineNo}: ${key} has an empty value` });
    if (/\s/.test(value) && !/^(['"]).*\1$/.test(value)) issues.push({ level: "warn", text: `Line ${lineNo}: quote values that contain spaces` });
    if (/(SECRET|TOKEN|KEY|PASSWORD)/.test(key) && value.replace(/^['"]|['"]$/g, "").length < 12) issues.push({ level: "warn", text: `Line ${lineNo}: ${key} looks short for a secret` });
  });
  if (!issues.length) issues.push({ level: "ok", text: "No obvious .env issues found." });
  return issues;
}

export function EnvValidatorUI() {
  const [input, setInput] = useState("API_URL=https://privatools.me\nSECRET_KEY=change-me\nFEATURE_FLAG=true\nBAD NAME=value");
  const issues = useMemo(() => parseEnv(input), [input]);
  const report = issues.map(item => `[${item.level.toUpperCase()}] ${item.text}`).join("\n");
  return (
    <SplitTool
      note="Checks .env syntax, duplicate keys, empty values, unquoted spaces, and suspiciously short secrets locally."
      left={<Field label=".env input"><TextArea value={input} onChange={setInput} /></Field>}
      right={<><div className="pt-lab-toolbar"><span className="pt-lab-result-label">Validation report</span><CopyButton value={report} /></div><div className="space-y-2">{issues.map(item => <div key={item.text} className={cn("rounded-lg border px-3 py-2 text-[13px]", statusClass(item.level))}>{item.text}</div>)}</div></>}
    />
  );
}

export function JsonCsvSchemaUI() {
  const [input, setInput] = useState('[{"id":1,"email":"a@example.com","active":true},{"id":2,"email":"b@example.com","active":false,"plan":"pro"}]');
  const result = useMemo(() => {
    try {
      const parsed = JSON.parse(input);
      const records = Array.isArray(parsed) ? parsed : [parsed];
      if (records.some(item => !item || typeof item !== "object" || Array.isArray(item))) throw new Error("Use an object or an array of objects.");
      const rows = records.map(item => flattenObject(item));
      const columns = Array.from(rows.reduce((set, row) => {
        Object.keys(row).forEach(key => set.add(key));
        return set;
      }, new Set<string>()));
      const csv = [columns.map(csvEscape).join(","), ...rows.map(row => columns.map(key => csvEscape(row[key])).join(","))].join("\n");
      const schema = columns.map(key => {
        const values = rows.map(row => row[key]);
        const filled = values.filter(value => value !== undefined && value !== null && value !== "").length;
        return `${key}: ${inferType(values)} (${filled}/${rows.length} rows)`;
      }).join("\n");
      return { csv, schema, error: "" };
    } catch (error) {
      return { csv: "", schema: "", error: (error as Error).message };
    }
  }, [input]);
  return (
    <div className="pt-specialist pt-dev-specialist space-y-4">
      <ClientOnlyNote>Flattens JSON objects, infers a lightweight schema, and exports CSV entirely in your browser.</ClientOnlyNote>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card/60 p-4">
          <Field label="JSON input"><TextArea value={input} onChange={setInput} rows={16} /></Field>
        </div>
        <div className="pt-specialist pt-dev-specialist space-y-4">
          <div className="rounded-2xl border border-border bg-card/60 p-4">
            <div className="pt-lab-toolbar"><span className="pt-lab-result-label">Inferred schema</span><CopyButton value={result.schema} /></div>
            <OutputBox value={result.error || result.schema} minHeight="min-h-[140px]" />
          </div>
          <div className="rounded-2xl border border-border bg-card/60 p-4">
            <div className="pt-lab-toolbar"><span className="pt-lab-result-label">CSV output</span><div className="flex gap-2"><CopyButton value={result.csv} /><DownloadButton value={result.csv} filename="data.csv" /></div></div>
            <OutputBox value={result.csv} minHeight="min-h-[160px]" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function JsonToCsvSchemaUI() {
  return <JsonCsvSchemaUI />;
}
