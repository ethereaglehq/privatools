export function formatMediaTime(seconds:number){const ms=Math.round(Math.max(0,seconds)*1000),h=Math.floor(ms/3600000),m=Math.floor(ms/60000)%60,s=Math.floor(ms/1000)%60;return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}${ms%1000?'.'+String(ms%1000).padStart(3,'0'):''}`;}

export function parseMediaTime(value:string){const match=value.trim().match(/^(\d+):([0-5]\d):([0-5]\d)(?:\.(\d{1,3}))?$/);return match?Number(match[1])*3600+Number(match[2])*60+Number(match[3])+(match[4]?Number('0.'+match[4]):0):NaN;}
