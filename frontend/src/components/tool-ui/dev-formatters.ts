const SQL_KEYWORDS = [
  "select", "from", "where", "group by", "order by", "having", "limit", "offset", "inner join",
  "left join", "right join", "full join", "cross join", "join", "on", "union", "values", "insert into",
  "update", "set", "delete from", "create table", "alter table",
];

export function formatSql(input: string) {
  // Protect quoted literals, identifiers and comments before changing whitespace.
  // This is a layout formatter, not a SQL parser or validator.
  const protectedParts: string[] = [];
  const marker = "\uE000";
  if (input.includes(marker)) return input;
  let formatted = input.replace(/'(?:''|\\.|[^'\\])*'|"(?:""|\\.|[^"\\])*"|`(?:``|\\.|[^`\\])*`|\[(?:\]\]|[^\]])*\]|--[^\r\n]*(?:\r?\n|$)|\/\*[\s\S]*?\*\//g, token => {
    const index = protectedParts.push(token) - 1;
    return `${marker}${index}${marker}`;
  }).replace(/\s+/g, " ").trim();
  if (!formatted) return "";
  // Match complete clauses once so JOIN does not reformat the tail of LEFT JOIN.
  const clauses = SQL_KEYWORDS.slice().sort((a, b) => b.length - a.length).map(k => k.replace(/ /g, "\\s+"));
  formatted = formatted.replace(new RegExp(`\\b(${clauses.join("|")})\\b`, "gi"), match => `\n${match.toUpperCase().replace(/\s+/g, " ")}`)
    .replace(/,\s*/g, ",\n  ").replace(/\s+(AND|OR)\s+/gi, "\n  $1 ").replace(/\n\s*\n/g, "\n").trim();
  return formatted.replace(/\uE000(\d+)\uE000/g, (_match, index) => protectedParts[Number(index)]);
}

export function formatGraphql(input: string) {
  const comments: string[] = [];
  if (input.includes("\uE200")) return input;
  input = input.replace(/"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|#[^\n]*(?:\n|$)/g, value => { if (!value.startsWith("#")) return value; return `\uE200${comments.push(value) - 1}\uE200`; });
  let out = "";
  let indent = 0;
  let quote = "";
  let escape = false;
  const pad = () => "  ".repeat(Math.max(0, indent));
  for (const ch of input.trim()) {
    if (quote) {
      out += ch;
      if (escape) {
        escape = false;
      } else if (ch === "\\") {
        escape = true;
      } else if (ch === quote) {
        quote = "";
      }
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      out += ch;
      continue;
    }
    if (ch === "{" || ch === "[" || ch === "(") {
      out = out.trimEnd() + ` ${ch}\n`;
      indent += 1;
      out += pad();
    } else if (ch === "}" || ch === "]" || ch === ")") {
      indent -= 1;
      out = out.trimEnd() + `\n${pad()}${ch}`;
    } else if (ch === ",") {
      out = out.trimEnd() + ",\n" + pad();
    } else if (/\s/.test(ch)) {
      if (!out.endsWith(" ") && !out.endsWith("\n")) out += " ";
    } else {
      out += ch;
    }
  }
  return out.replace(/\s+\n/g, "\n").trim().replace(/\uE200(\d+)\uE200/g, (_match,index) => comments[Number(index)]);
}

function parseCronField(field: string, min: number, max: number) {
  const values = new Set<number>();
  for (const part of field.split(",")) {
    if (!/^(?:\*|\d+(?:-\d+)?)(?:\/\d+)?$/.test(part)) throw new Error(`Invalid cron field "${part}"`);
    const [rangePart, stepRaw] = part.split("/");
    const step = stepRaw ? Number(stepRaw) : 1;
    if (!Number.isInteger(step) || step < 1) throw new Error(`Invalid step in "${part}"`);
    let start = min;
    let end = max;
    if (rangePart !== "*") {
      const [a, b] = rangePart.split("-");
      start = Number(a);
      end = b === undefined ? (stepRaw ? max : start) : Number(b);
    }
    if (!Number.isInteger(start) || !Number.isInteger(end) || start < min || end > max || start > end) {
      throw new Error(`Invalid range "${part}"`);
    }
    for (let value = start; value <= end; value += step) values.add(value);
  }
  return values;
}

export function describeCronField(field: string, label: string, unit: string) {
  if (field === "*") return `Every ${unit}`;
  if (/^\*\/\d+$/.test(field)) return `Every ${field.slice(2)} ${unit}s`;
  if (/^\d+$/.test(field)) return `${label} ${field}`;
  return `${label}s ${field}`;
}

export function nextCronRuns(expr: string, after = new Date()) {
  const parts = expr.trim().split(/\s+/);
  if (parts.length !== 5) throw new Error("Use standard 5-field cron: minute hour day month weekday");
  const [minRaw, hourRaw, dayRaw, monthRaw, weekdayRaw] = parts;
  const minutes = parseCronField(minRaw, 0, 59);
  const hours = parseCronField(hourRaw, 0, 23);
  const days = parseCronField(dayRaw, 1, 31);
  const months = parseCronField(monthRaw, 1, 12);
  const weekdays = parseCronField(weekdayRaw, 0, 7);
  const runs: Date[] = [];
  const cursor = new Date(after);
  cursor.setSeconds(0, 0);
  cursor.setMinutes(cursor.getMinutes() + 1);
  const maxChecks = 60 * 24 * 370;
  for (let i = 0; i < maxChecks && runs.length < 5; i += 1) {
    const weekday = cursor.getDay();
    const weekdayMatch = weekdays.has(weekday) || (weekday === 0 && weekdays.has(7));
    if (
      minutes.has(cursor.getMinutes()) &&
      hours.has(cursor.getHours()) &&
      months.has(cursor.getMonth() + 1) &&
      (dayRaw.includes("*") || weekdayRaw.includes("*")
        ? days.has(cursor.getDate()) && weekdayMatch
        : days.has(cursor.getDate()) || weekdayMatch)
    ) {
      runs.push(new Date(cursor));
    }
    cursor.setMinutes(cursor.getMinutes() + 1);
  }
  return runs;
}

export function bumpSemver(version: string, kind: "major" | "minor" | "patch" | "prerelease") {
  const match = version.trim().replace(/^v/, "").match(/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/);
  if (!match) throw new Error("Use a version like 1.2.3 or v1.2.3-beta.1");
  const [, majorRaw, minorRaw, patchRaw] = match;
  let pre = match[4];
  let major = Number(majorRaw), minor = Number(minorRaw), patch = Number(patchRaw);
  if (![major, minor, patch].every(Number.isSafeInteger) || pre?.split(".").some(v => /^0\d+$/.test(v))) throw new Error("Version numbers must be safe integers without leading zeros.");
  if (kind === "major") { if (minor !== 0 || patch !== 0 || !pre) major++; minor = 0; patch = 0; pre = ""; }
  if (kind === "minor") { if (patch !== 0 || !pre) minor++; patch = 0; pre = ""; }
  if (kind === "patch") { if (!pre) patch++; pre = ""; }
  if (kind === "prerelease") {
    if (!pre) { patch++; pre = "beta.1"; }
    else { const ids = pre.split("."); let last = -1; for (let i = ids.length - 1; i >= 0; i--) { if (/^\d+$/.test(ids[i])) { last = i; break; } } if (last < 0) ids.push("1"); else { const number = Number(ids[last]) + 1; if (!Number.isSafeInteger(number)) throw new Error("Prerelease number is too large."); ids[last] = String(number); } pre = ids.join("."); }
  }
  if (![major, minor, patch].every(Number.isSafeInteger)) throw new Error("Version number is too large.");
  return `${major}.${minor}.${patch}${pre ? `-${pre}` : ""}`;
}
