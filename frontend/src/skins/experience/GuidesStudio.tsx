import { BlogIndexContent } from '@/pages/BlogPage';
import { BlogArticleContent } from '@/pages/BlogPostPage';

/**
 * The journal: the guide index at /blog and one guide at /blog/<slug>. Both
 * read data/blog.ts, every article's HTML, so SkinApp loads this module only
 * on blog routes (src/test/blog-module-boundary.test.ts and
 * scripts/check-bundle-size.mjs keep it off every other page).
 */
export default function GuidesStudio({slug,tag,onTag}:{slug?:string;tag:string;onTag:(v:string)=>void}){
 return slug ? <BlogArticleContent key={slug} slug={slug}/> : <BlogIndexContent tag={tag} onTagChange={onTag}/>;
}
