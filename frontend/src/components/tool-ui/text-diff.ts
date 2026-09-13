export interface DiffLine {
    type: "same" | "added" | "removed";
    text: string;
    lineA?: number;
    lineB?: number;
}

export function computeDiff(a: string, b: string): DiffLine[] {
    const left = a ? a.replace(/\r\n?/g,"\n").split("\n") : [], right = b ? b.replace(/\r\n?/g,"\n").split("\n") : [];
    const width = right.length + 1;
    if ((left.length + 1) * width > 4_000_000) throw new Error("Compare shorter sections (up to roughly 2,000 lines per side) to keep this editor responsive.");
    const table = new Uint32Array((left.length + 1) * width);
    for (let i = left.length - 1; i >= 0; i--) for (let j = right.length - 1; j >= 0; j--) table[i*width+j] = left[i] === right[j] ? table[(i+1)*width+j+1]+1 : Math.max(table[(i+1)*width+j],table[i*width+j+1]);
    const result: DiffLine[] = []; let i=0,j=0;
    while(i<left.length || j<right.length) {
        if(i<left.length && j<right.length && left[i]===right[j]) { result.push({type:"same",text:left[i],lineA:++i,lineB:++j}); }
        else if(j>=right.length || (i<left.length && table[(i+1)*width+j]>=table[i*width+j+1])) result.push({type:"removed",text:left[i],lineA:++i});
        else result.push({type:"added",text:right[j],lineB:++j});
    }
    return result;
}
