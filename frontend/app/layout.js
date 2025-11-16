import "./globals.css";

export const metadata = {
  title: "Research Paper Analyzer",
  description: "Analyze research papers in three passes",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
