import { Suspense } from "react";
import { Header } from "@/components/header/Header";
import { ToolCardGrid } from "@/components/tool-card";
import { AuthErrorBanner } from "@/components/auth/AuthErrorBanner";
import { getTools } from "@/lib/api/tools";
import { ToolRead } from "@/lib/api/types";

export default async function CatalogPage() {
  let tools: ToolRead[] = [];
  let fetchError = false;

  try {
    tools = await getTools();
  } catch {
    fetchError = true;
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      <Header />
      <Suspense>
        <AuthErrorBanner />
      </Suspense>

      <main className="mx-auto max-w-7xl px-6 py-16">
        <div className="mb-16 text-center">
          <h1 className="mb-4 bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-5xl font-bold text-transparent">
            Discover AI Tools
          </h1>
          <p className="text-lg text-zinc-400">
            Run powerful agents directly in your browser
          </p>
        </div>

        {fetchError ? (
          <p className="text-center text-zinc-500">
            Could not load tools. Please refresh the page.
          </p>
        ) : (
          <ToolCardGrid tools={tools} />
        )}
      </main>
    </div>
  );
}
