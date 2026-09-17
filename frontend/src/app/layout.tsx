import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Log Analyzer",
  description: "Upload logs, detect anomalies, query with natural language",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
