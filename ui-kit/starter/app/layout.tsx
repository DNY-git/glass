import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sports Looking Glass — viewer",
  description:
    "Read-only viewer over the Sports Looking Glass deterministic football analysis store. Estimates, never promises.",
};

const NAV = [
  { href: "/", label: "Forecasts" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/provenance", label: "Provenance" },
  { href: "/methodology", label: "Methodology" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between flex-wrap gap-2">
            <Link href="/" className="font-semibold text-slate-800">
              Sports Looking Glass <span className="text-slate-400 font-normal">· viewer</span>
            </Link>
            <nav className="flex gap-1 text-sm">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="px-3 py-1.5 rounded text-slate-600 hover:bg-slate-100 hover:text-indigo-700"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="border-t border-slate-200 mt-12">
          <div className="mx-auto max-w-5xl px-4 py-4 text-xs text-slate-400">
            Read-only viewer over a deterministic, write-once store. Estimates,
            never promises; this system never places or assists bets.
          </div>
        </footer>
      </body>
    </html>
  );
}
