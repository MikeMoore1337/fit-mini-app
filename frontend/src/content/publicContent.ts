import manifest from './publicContent.json';

export interface PublicContentLink {
  path: string;
  label: string;
  description?: string;
}

export interface PublicContentSection {
  heading: string;
  paragraphs: string[];
  points?: string[];
}

export interface PublicContentSource {
  title: string;
  publisher: string;
  url: string;
}

export interface PublicContentPage {
  kind: 'landing' | 'product' | 'knowledge-index' | 'guide';
  path: string;
  category?: string;
  title: string;
  description: string;
  ogDescription: string;
  eyebrow: string;
  heading: string;
  intro: string;
  highlights?: string[];
  sections: PublicContentSection[];
  related: PublicContentLink[];
  cta?: {
    label: string;
    description: string;
  };
  breadcrumbs: PublicContentLink[];
  updated?: string;
  author?: {
    name: string;
    type: 'Organization' | 'Person';
  };
  reviewer?: {
    name: string;
    type: 'Organization' | 'Person';
  } | null;
  disclaimer?: string;
  sources?: PublicContentSource[];
}

export interface PublicContentCategory {
  slug: string;
  label: string;
  description: string;
}

interface PublicContentManifest {
  categories: PublicContentCategory[];
  pages: PublicContentPage[];
}

export const publicContent = manifest as PublicContentManifest;

export function getPublicContentPage(path: string): PublicContentPage | undefined {
  return publicContent.pages.find((page) => page.path === path);
}

export function isPublicContentPath(path: string): boolean {
  const page = getPublicContentPage(path);
  return page !== undefined && page.kind !== 'landing';
}

export function publicGuides(): PublicContentPage[] {
  return publicContent.pages.filter((page) => page.kind === 'guide');
}

export function categoryForSlug(slug: string | undefined): PublicContentCategory | undefined {
  return publicContent.categories.find((category) => category.slug === slug);
}
