import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/QueryProvider";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "CV Maker - AI Powered Application Assistant",
  description: "Create professional CVs and Cover Letters tailored to job descriptions using AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100`}
      >
        <QueryProvider>
          <Navbar />
          <main className="pt-24 pb-12 px-4 max-w-7xl mx-auto">
            {children}
          </main>
        </QueryProvider>
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
