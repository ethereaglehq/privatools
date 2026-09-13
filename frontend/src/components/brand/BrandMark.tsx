import { brandGeometry } from './geometry';

export function BrandMark({ className }: { className?: string }) {
  return <svg className={className} viewBox="0 0 48 56" fill="currentColor" aria-hidden="true" focusable="false">
    {brandGeometry.map(piece => <path key={piece.slug} d={piece.path} />)}
  </svg>;
}
