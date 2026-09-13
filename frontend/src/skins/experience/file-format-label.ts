export function fileFormatLabel(accepts?: string) {
    const first = (accepts?.split(",")[0] || "file").trim();
    if (first === "*" || first === "*/*") return "FILE";
    if (first.endsWith("/*")) return first.split("/")[0].toUpperCase();
    return first.replace(/^\./, "").split("/").pop()?.replace("jpeg", "jpg").toUpperCase() || "FILE";
}
