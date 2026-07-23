import type { Metadata } from "next";
import Link from "next/link";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Contractor Bot Dashboard",
  description: "Lead management and configuration dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 antialiased">
        <nav className="border-b border-gray-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3 sm:px-6 lg:px-8">
            <span className="text-lg font-bold text-indigo-600">Contractor Bot</span>
            <Link
              href="/leads"
              className="text-sm font-medium text-gray-600 hover:text-indigo-600"
            >
              Leads
            </Link>
            <Link
              href="/config"
              className="text-sm font-medium text-gray-600 hover:text-indigo-600"
            >
              Config
            </Link>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
        <Analytics />
      </body>
    </html>
  );
}
