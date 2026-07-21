import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIZS ChatGPT Style",
  description: "AIZS Campus Consulting Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#212121] text-white">
        {children}
      </body>
    </html>
  );
}
