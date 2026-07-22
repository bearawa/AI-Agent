import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ZUEL Campus AI Assistant",
  description: "Zhongnan University of Economics and Law (中南财经政法大学) Campus Consulting Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-gray-900 text-white">
        {children}
      </body>
    </html>
  );
}
