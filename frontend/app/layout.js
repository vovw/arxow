import "./globals.css";

export const metadata = {
  title: "Arxow - Research Paper Analyzer",
  description: "AI-powered research paper analysis using three-pass method",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
