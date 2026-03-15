"use client";

import { Highlight, themes } from "prism-react-renderer";

const LANG_MAP: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  go: "go",
  rust: "rust",
  java: "java",
  c: "c",
  cpp: "cpp",
  csharp: "csharp",
  ruby: "ruby",
  php: "php",
  swift: "swift",
  kotlin: "kotlin",
  sql: "sql",
  bash: "bash",
  shell: "bash",
  json: "json",
  yaml: "yaml",
  html: "markup",
  css: "css",
};

export function resolveLanguage(lang?: string): string {
  if (!lang) return "typescript";
  const key = lang.toLowerCase().trim();
  return LANG_MAP[key] ?? "typescript";
}

export { themes } from "prism-react-renderer";
export { Highlight } from "prism-react-renderer";

export function SyntaxHighlighter({
  code,
  language,
  className: wrapperClassName,
}: {
  code: string;
  language?: string;
  className?: string;
}) {
  const resolvedLang = resolveLanguage(language);

  return (
    <Highlight theme={themes.oneDark} code={code.trimEnd()} language={resolvedLang}>
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <pre
          className={`overflow-x-auto rounded-lg p-3 text-xs leading-relaxed ${wrapperClassName ?? ""}`}
          style={{ ...style, background: "rgb(17 17 17)" }}
        >
          <code className={className}>
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })}>
                <span className="mr-4 inline-block w-8 select-none text-right text-zinc-600">
                  {i + 1}
                </span>
                {line.map((token, key) => (
                  <span key={key} {...getTokenProps({ token })} />
                ))}
              </div>
            ))}
          </code>
        </pre>
      )}
    </Highlight>
  );
}
