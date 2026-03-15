"use client";

import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";

const components: Components = {
  h1: ({ children }) => (
    <h1 className="text-2xl font-bold text-white mt-0 mb-4">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-semibold text-white mt-6 mb-2 pb-1 border-b border-zinc-700">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold text-zinc-200 mt-4 mb-1">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="text-sm text-zinc-300 leading-relaxed mb-3">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc list-inside space-y-1 mb-3 text-sm text-zinc-300">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-inside space-y-1 mb-3 text-sm text-zinc-300">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-violet-400 hover:text-violet-300 underline underline-offset-2 break-all"
    >
      {children}
    </a>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-white">{children}</strong>
  ),
  em: ({ children }) => <em className="italic text-zinc-300">{children}</em>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-violet-500 pl-4 my-3 text-zinc-400 italic">
      {children}
    </blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs font-mono text-violet-300">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="rounded-lg bg-zinc-800 p-4 overflow-x-auto text-xs font-mono text-zinc-300 mb-3">
      {children}
    </pre>
  ),
  hr: () => <hr className="border-zinc-700 my-4" />,
};

export function MarkdownReport({ content }: { content: string }) {
  return <ReactMarkdown components={components}>{content}</ReactMarkdown>;
}
