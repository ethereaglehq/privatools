/** One source for a tool page's title, H1 and description. The server reads the same registry fields through the build manifest. */
export interface ToolSeoInput { name: string; seoTitle?: string; metaDescription?: string; longDescription?: string; description?: string }
export interface ToolSeo { title: string; h1: string; description: string }

export function toolSeo(tool: ToolSeoInput): ToolSeo {
  const title = tool.seoTitle?.trim();
  return {
    title: title || `${tool.name} — Free Online | PrivaTools`,
    h1: title || tool.name,
    description: tool.metaDescription?.trim() || tool.longDescription || tool.description || "",
  };
}
