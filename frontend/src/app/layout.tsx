import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { QueryProvider } from "@/components/providers/QueryProvider";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Market — Discover and Run AI Tools",
  description:
    "A marketplace of AI-powered tools. Run research agents, code reviewers, document Q&A, and more — directly in your browser.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-white antialiased`}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
