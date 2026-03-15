"use client";

import Editor from "react-simple-code-editor";
import { Highlight, themes } from "prism-react-renderer";
import { resolveLanguage } from "./syntax-highlighter";

export function CodeInput({
  value,
  onChange,
  language,
  placeholder = "Paste your code here...",
}: {
  value: string;
  onChange: (code: string) => void;
  language?: string;
  placeholder?: string;
}) {
  const lang = resolveLanguage(language);

  const highlight = (code: string) => {
    if (!code) return "";
    return (
      <Highlight theme={themes.oneDark} code={code} language={lang}>
        {({ tokens, getTokenProps }) =>
          tokens.map((line, i) => (
            <span key={i}>
              {line.map((token, key) => (
                <span key={key} {...getTokenProps({ token })} />
              ))}
              {i < tokens.length - 1 ? "\n" : ""}
            </span>
          ))
        }
      </Highlight>
    );
  };

  return (
    <div className="relative rounded-lg border border-zinc-700 bg-zinc-800 font-mono text-sm focus-within:border-violet-500 transition-colors">
      <Editor
        value={value}
        onValueChange={onChange}
        highlight={highlight as unknown as (code: string) => string}
        placeholder={placeholder}
        padding={12}
        style={{
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          fontSize: 14,
          lineHeight: 1.6,
          minHeight: 280,
          color: "#d4d4d4",
          caretColor: "#d4d4d4",
        }}
        className="code-input-editor"
        textareaClassName="code-input-textarea"
      />
      <style jsx global>{`
        .code-input-editor {
          background: transparent !important;
        }
        .code-input-textarea {
          outline: none !important;
        }
        .code-input-textarea::placeholder {
          color: rgb(113 113 122);
        }
      `}</style>
    </div>
  );
}
